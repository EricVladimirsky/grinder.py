# A simple example using the HTTP plugin that shows the retrieval of a
# single file via HTTP.
#
from java.util import Random

from net.grinder.script import Test
from net.grinder.plugin.http import HTTPRequest
from net.grinder.script.Grinder import grinder


seed = grinder.getProperties()['grinder.seed']
if seed:
    random = Random(int(seed))
else:
    random = Random()


test1 = Test(1, "Localhost")
request1 = test1.wrap(HTTPRequest())


class TestRunner:
    def __call__(self):
        i = random.nextInt(100)
        url = 'http://localhost?%s' % i
        request1.GET(url)

