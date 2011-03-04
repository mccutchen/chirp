"""A generic, simple, potentially-dumb wrapper around Twitter's RESTful
API. Attribute accesses are translated into path components in API URLs,
method calls are translated into HTTP requests. All calls are made to the JSON
endpoints.

At the moment, only GET requests not requiring authentication will work. TODO:
Optionally support OAuth?

Some examples:

    >>> api = TwitterAPI()

    # GET http://api.twitter.com/1/statuses/public_timeline.json
    >>> api.statuses.public_timeline.get()

    # GET http://api.twitter.com/1/statuses/public_timeline.json?trim_user=1
    >>> api.statuses.public_timeline.get(trim_user=True)

    # GET http://api.twitter.com/1/statuses/show/2404341.json
    >>> api.statuses.show(2404341).get()

    # GET http://api.twitter.com/1/statuses/2404341/retweeted_by.json
    >>> api.statuses(2404341).retweeted_by.get()

    # GET http://api.twitter.com/1/statuses/2404341/retweeted_by.json?page=3
    >>> api.statuses(2404341).retweeted_by.get(page=3)

    # GET http://api.twitter.com/1/trends/current.json
    >>> api.trends.current.get()

    # http://api.twitter.com/1/trends/current.json?exclude=hashtags >>>
    api.trends.current.get(exclude='hashtags')

Any other HTTP method will raise an exception.
"""

import httplib
import logging
import os
import re
import sys
import urllib

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        try:
            from django.utils import simplejson
        except ImportError:
            raise ImportError, 'Unable to load a json library'


API_HOST = 'api.twitter.com'
URL_TEMPLATE = '/1/%s.json'


class TwitterAPI(object):
    """A simple wrapper around the Twitter API."""

    def __init__(self, paths=None):
        self.paths = paths or tuple()

    def __getattr__(self, name):
        return self(name)

    def __call__(self, name):
        return TwitterAPI(self.paths + (str(name),))

    def get(self, **kwargs):
        return self._request('get', **kwargs)

    def post(self, **kwargs):
        return self._request('post', **kwargs)

    def put(self, **kwargs):
        return self._request('put', **kwargs)

    def delete(self, **kwargs):
        return self._request('delete', **kwargs)

    def _request(self, method, **kwargs):
        """Makes a request to the Twitter API using the given HTTP method and
        the current set of path components for this object. Any kwargs will be
        used as request parameters (appended to the URL for GET requests, sent
        in the request body otherwise).
        """
        url, body = build_url(method, self.paths, **kwargs)
        return make_request(method, url, body)


class TwitterError(Exception):
    pass


class AttrDict(dict):
    """A dict subclass that allows access to keys via normal item access and
    via attribute access.  E.g. d['key'] == d.key.
    """
    def __getattr__(self, name):
        if name not in self:
            return super(AttrDict, self).__getattr__(name)
        return self[name]

    def __repr__(self):
        return 'AttrDict(%s)' % super(AttrDict, self).__repr__()


##############################################################################
# Helper functions
##############################################################################
def build_url(method, paths, **kwargs):
    """Builds an appropriate Twitter API URL to request. Returns a 2-tuple of
    (url, request body).

    The URL will be built as follows: The given paths be joined with slashes
    and inserted into the URL_TEMPLATE string. Any kwargs are interpreted as
    request parameters and will be appended to the URL for GET requests or
    treated as the request body otherwise.
    """
    url = URL_TEMPLATE % '/'.join(paths)
    params = preprocess_params(kwargs)
    if method == 'get':
        if params:
            url += '?' + urllib.urlencode(params)
        body = None
    else:
        body = urllib.urlencode(params) if params else None
    return url, body

def preprocess_params(params):
    """Preprocess request parameters. Only transforms bools into the
    appropriate strings, at the moment.
    """
    processed = dict(params)
    for k, v in processed.iteritems():
        if isinstance(v, bool):
            processed[k] = str(int(v))
    return processed

def make_request(method, url, body, headers=None, parse_json=True):
    """Makes an HTTP request. Responses are assumed to be JSON, and will be
    parsed as such.
    """
    logging.info('Request: %s %s', method.upper(), url)
    if body:
        logging.info('Request body: %r', body)
    conn = httplib.HTTPConnection(API_HOST)
    conn.request(method.upper(), url, body)
    resp = conn.getresponse()
    if resp.status != 200:
        raise TwitterError('Bad Response: %s %s' % (resp.status, resp.reason))
    if parse_json:
        return json.load(resp, object_hook=AttrDict)
    else:
        return resp.read()


if __name__ == '__main__':
    api = TwitterAPI()
    print api.statuses.public_timeline.get(trim_user=True)
