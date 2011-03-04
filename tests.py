import logging
import os
import sys
import unittest

import chirp


class ChirpTests(unittest.TestCase):

    def setUp(self):
        self.api = chirp.TwitterAPI()

    def test_attr_access(self):
        new_api = self.api.a.b.c.d.e.f
        self.assertEqual(len(new_api.paths), 6)

    def test_call_access(self):
        new_api = self.api(1)(2)(3)(4)
        self.assertEqual(len(new_api.paths), 4)

    def test_mixed_access(self):
        new_api = self.api.a(1).b(2).c(3)
        self.assertEqual(len(new_api.paths), 6)

    def test_preprocess_params(self):
        a = dict(a=1, b=2, c=True)
        b = chirp.preprocess_params(a)
        self.assertNotEqual(a, b)
        self.assertEqual(b['c'], '1')

        c = dict(a=1, b=2, c=False)
        d = chirp.preprocess_params(c)
        self.assertNotEqual(c, d)
        self.assertEqual(d['c'], '0')

    def test_build_get_url(self):
        new_api = self.api.statuses.public_timeline
        url, body = chirp.build_url('get', new_api.paths)
        self.assertEqual(url, '/1/statuses/public_timeline.json')
        self.assertEqual(body, None)

    def test_build_get_url_with_params(self):
        new_api = self.api.statuses.public_timeline
        url, body = chirp.build_url('get', new_api.paths, trim_user=True)
        self.assertEqual(url, '/1/statuses/public_timeline.json?trim_user=1')
        self.assertEqual(body, None)

    def test_build_post_url(self):
        new_api = self.api.statuses.update
        url, body = chirp.build_url('post', new_api.paths, status='Hello!')
        self.assertEqual(url, '/1/statuses/update.json')
        self.assertEqual(body, 'status=Hello%21')

    def test_public_twitter_api(self):
        resp = self.api.statuses.public_timeline.get()
        self.assertEqual(len(resp), 20)

    def test_public_twitter_api_with_params(self):
        resp = self.api.statuses.public_timeline.get(trim_user=True)
        self.assertEqual(len(resp), 20)
        self.assertTrue(isinstance(resp[0]['user']['id'], (int,long)))

    def test_private_twitter_api(self):
        self.assertRaises(
            chirp.TwitterError,
            self.api.statuses.update.post, status='Hello?')


if __name__ == '__main__':
    unittest.main()

