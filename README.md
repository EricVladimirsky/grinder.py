grinder.py
==========

A python wrapper for grinder 3's http api

Rather than use a horrible swing-based console, grinder.py's goal is to
make load testing fun again.

Preparation
-----------

First install grinder v3 via sourceforge: 

   http://sourceforge.net/projects/grinder/files/latest/download

Then install it by unzipping to ``/usr/local/grinder``

Launch a headless console via:

    java -cp /usr/local/grinder/lib/grinder.jar net.grinder.Console -headless


Launch workers (each in its own temporary directory):

    java -cp /usr/local/grinder/lib/grinder.jar net.grinder.Grinder


grinder.py uses a few python libraries:

    pip install -r tools/pip-requires


Run a test job
--------------

Your job and job property file (grinder.properties) should be in a directory.
To launch your job:

    ./grinder.py (path to job) --runs 42

I've included a sample job that should work as long as you have a web server
running on localhost.

    $ ./grinder.py sample/ --runs 42
    | stopping existing work
    | configured job
    workers	tests
    0	0
    0	0
    1	0
    1	3
    1	6
    1	9
    1	13
    1	16
    1	20
    1	23
    1	26
    1	30
    1	33
    1	36
    1	42
    +-----------------------------------+----------------+
    | metric                            | value          |
    +-----------------------------------+----------------+
    | Tests                             | 42             |
    | Errors                            | 0              |
    | Mean Test Time (ms)               | 311.595238095  |
    | Test Time Standard Deviation (ms) | 67.9625455407  |
    | TPS                               | 3.22605422844  |
    | Peak TPS                          | 4.0            |
    | Mean response length              | 1651.0         |
    | Response bytes per second         | 5326.21553115  |
    | Response errors                   | 0              |
    | Mean time to resolve host         | 0.047619047619 |
    | Mean time to establish connection | 0.309523809524 |
    | Mean time to first byte           | 309.261904762  |
    +-----------------------------------+----------------+


License
-------

Apache
