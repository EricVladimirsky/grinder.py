#!/usr/bin/env python

import argparse
import json
import os
import sys
import time

import prettytable
import requests


class Grinder(object):
    """Controls a headless Grinder v3

    Headless griders are started via:

        java -cp lib/grinder.jar net.grinder.Console -headless
    """

    # PLUMBING

    def __init__(self, host='http://localhost:6373'):
        """Creates a new controller pointing to a grinder console"""
        self._host = host

    def _url(self, path):
        return '%s/%s' % (self._host, path)

    def _get(self, path):
        """send a http json get"""
        r = requests.get(self._url(path))
        assert r.status_code == 200
        return r.json

    def _post(self, path, data=None):
        """send a http json post"""
        headers = {'content-type': 'application/json'}
        if data:
            data = json.dumps(data)
        r = requests.post(self._url(path), data=data, headers=headers)
        assert r.status_code == 200
        return r

    def _put(self, path, data=None):
        """send a http json put"""
        headers = {'content-type': 'application/json'}
        if data:
            data = json.dumps(data)
        r = requests.put(self._url(path), data=data, headers=headers)
        assert r.status_code == 200
        return r

    def workers_start(self, properties=None):
        """Send a start signal to the agents to start worker processes.

        optionally send properties dict which override distributed properties
        file"""
        self._post('agents/start-workers', properties)

    def agents_stop(self):
        """Terminates all agents and their worker processes.

        You usually want to run workers_reset instead."""
        self._post('agents/stop')

    def workers_reset(self):
        """send a stop signal to connected worker processes"""
        self._post('agents/stop-workers')

    def agents_status(self):
        """return the status of the agent and worker processes"""
        return self._get('agents/status')

    def properties_get(self):
        """Return the current values of the console options."""
        return self._get('properties')

    def properties_set(self, properties):
        """Set console options.

        The body of the request should be a map of keys to new values; you can
        provide some or all of the properties. A map of the keys and their new
        values will be returned. You can find out the names of the keys by
        issuing a GET to /properties."""
        self._put('properties', properties)

    def files_distribute(self):
        """Start the distribution of files to agents with out of date cache.

        Distribution may take some time, so the service will return
        immediately and the files will be distributed in proceeds in the
        background. The service returns a map with an :id entry that can be
        used to identify the particular distribution request."""
        self._post('files/distribute')

    def files_status(self):
        """Returns whether the agent caches are stale

        (i.e. they are out of date with respect to the console's central copy
        of the files), and the status of the last file distribution."""
        return self._get('files/status')

    def recording_data(self):
        """Return the current recorded data"""
        return self._get('recording/data')

    def recording_reset(self):
        """Discard all recorded data.

        After a reset, the model loses all knowledge of Tests; this can be
        useful when swapping between scripts.  It makes sense to reset with
        the worker processes stopped."""
        self._post('recording/reset')

    def recording_start(self):
        """Start capturing data.

        An initial number of samples may be ignored, depending on the
        configured properties."""
        self._post('recording/start')

    def recording_stop(self):
        """Stop the data capture"""
        self._post('recording/stop')

    def recording_status(self):
        """Return the current recording status"""
        return self._get('recording/status')

    # PORCELAIN

    def job_set(self, path):
        """Configure grinder for a job.

        Job files and grinder.properties should be located in path"""
        properties = {
            'distributionDirectory': path,
            'propertiesFile': 'grinder.properties'
        }
        self.properties_set(properties)

    def workers_ready(self, qty=None):
        """Test if workers are ready.

        If qty is specified check if specified number of agents are present"""
        agents = self.agents_status()
        if any([a['state'] != 'RUNNING' for a in agents]):
            return False
        if qty and len(agents) != qty:
            return False
        return True

    def workers_status(self):
        """Return a list of all workers for all agents"""
        workers = []
        for agent in self.agents_status():
            workers += agent['workers']
        return workers

    def total_samples(self):
        """return total number of samples collected from all tests"""

        totals = self.recording_data()['totals']
        return totals[0] + totals[1]

    def start(self, runs=None, threads=None, processes=None, seed=None):
        properties = {}
        if runs:
            properties['grinder.runs'] = runs
        if threads:
            properties['grinder.threads'] = threads
        if processes:
            properties['grinder.processes'] = processes
        if seed:
            properties['grinder.seed'] = seed
        self.workers_start(properties)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run some tests yo.')
    parser.add_argument('job_path', type=str, nargs=1,
                   help='path to grinder job')
    parser.add_argument('--runs', type=int, nargs='?', default=1,
                   help='number of runs of test')
    parser.add_argument('--threads', type=int, nargs='?', default=1,
                   help='number of threads per agent')
    parser.add_argument('--seed', type=int, nargs='?',
                   help='seed sent to tests as grinder.seed property')
    parser.add_argument('--processes', type=int, nargs='?', default=1,
                   help='number of processes per agent')
    args = parser.parse_args()

    g = Grinder()

    job_path = os.path.abspath(args.job_path[0])
    if not os.path.exists(job_path):
        print "Directory doesn't exist: %s" % job_path
        sys.exit(1)
    if not os.path.exists(os.path.join(job_path, 'grinder.properties')):
        print "Couldn't find grinder.properties in: %s" % job_path
        sys.exit(1)

    print "| stopping existing work"

    # STOP EVERYTHING
    g.workers_reset()
    g.recording_reset()

    # SETUP EVERYTHING
    g.job_set(job_path)
    g.files_distribute()

    while g.files_status()['stale']:
        time.sleep(0.1)

    while not g.workers_ready():
        time.sleep(0.1)

    print "| configured job"

    # START WORK
    g.recording_start()
    g.start(args.runs, args.threads, args.processes, args.seed)

    print "\t".join(['workers', 'tests'])
    # FIXME(ja): THIS IS WRONG in the case where a run outputs multiple samples
    # eg, has multiple tests
    i = 0
    start = time.time()
    while g.total_samples() < args.runs:
        if i % 10 == 0:
            print 'timer\ttests\tTPS\terrors\tmean ms\tstddev\tsize KB\tKBps'
        i += 1
        d = g.recording_data()['totals']
        print '%0.0f\t%d\t%0.1f\t%d\t%0.1f\t%0.1f\t%0.1f\t%0.1f' % (time.time() - start, d[0], float(d[4]), d[1], float(d[2]), float(d[3]), float(d[6])/1024, float(d[7])/1024)
        time.sleep(1)

    g.recording_stop()
    data = g.recording_data()
    g.workers_reset()

    pt = prettytable.PrettyTable()
    pt.add_column('metric', data['columns'], align='l')
    pt.add_column('value', data['totals'], align='l')
    print pt

    while len(g.workers_status()) > 0:
        time.sleep(0.1)
