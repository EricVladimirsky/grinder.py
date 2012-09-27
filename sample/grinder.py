# A simple example using the HTTP plugin that shows the retrieval of a
# single file via HTTP.
#
from java.util import Random

from net.grinder.script import Test
from net.grinder.plugin.http import HTTPRequest


test1 = Test(1, "Localhost")
request1 = test1.wrap(HTTPRequest())
random = Random()

class TestRunner:
    def __call__(self):
        i = abs(random.nextInt()) % 999
        url = 'http://localhost?%d' % i
        request1.GET(url)

