# -*- coding: utf-8 -*-
"""
Test pylti/common.py module
"""
from pylti.common import LTIOAuthDataStore, verify_request_common
import unittest
from oauth import oauth


class TestCommandLine(unittest.TestCase):
    consumers = {
        "key1": {"secret": "secret1"},
        "key2": {"secret": "secret2"},
        "key3": {"secret": "secret3"},
        "keyNS": {}
    }

    def test_LTIOAuthDataStore(self):
        store = LTIOAuthDataStore(self.consumers)
        self.assertEqual(store.lookup_consumer("key1").secret, "secret1")
        self.assertEqual(store.lookup_consumer("key2").secret, "secret2")
        self.assertEqual(store.lookup_consumer("key3").secret, "secret3")
        self.assertIsNone(store.lookup_consumer("key4"))
        self.assertIsNone(store.lookup_consumer("keyNS"))


    def test_verify_request_common(self):
        consumers = {
            "__consumer_key__": {"secret": "__lti_secret__"}
        }
        url = 'http://localhost:5000/?'
        method = 'GET'
        headers = dict()
        params = {'resource_link_id': u'edge.edx.org-i4x-MITx-ODL_ENG-lti-94173d3e79d145fd8ec2e83f15836ac8',
                  'user_id': u'008437924c9852377e8994829aaac7a1',
                  'roles': u'Instructor',
                  'lis_result_sourcedid': u'MITx/ODL_ENG/2014_T1:edge.edx.org-i4x-MITx-ODL_ENG-lti-94173d3e79d145fd8ec2e83f15836ac8:008437924c9852377e8994829aaac7a1',
                  'context_id': u'MITx/ODL_ENG/2014_T1',
                  'lti_version': u'LTI-1p0',
                  'launch_presentation_return_url': u'',
                  'lis_outcome_service_url': u'https://edge.edx.org/courses/MITx/ODL_ENG/2014_T1/xblock/i4x:;_;_MITx;_ODL_ENG;_lti;_94173d3e79d145fd8ec2e83f15836ac8/handler_noauth/grade_handler',
                  'lti_message_type': u'basic-lti-launch-request',
        }
        store = LTIOAuthDataStore(consumers)
        import urllib

        urlparams = urllib.urlencode(params)
        import oauthlib.oauth1

        client = oauthlib.oauth1.Client('__consumer_key__', client_secret='__lti_secret__',
                                        signature_method=oauthlib.oauth1.SIGNATURE_HMAC,
                                        signature_type=oauthlib.oauth1.SIGNATURE_TYPE_QUERY)
        signature = client.sign("{}{}".format(url, urlparams))
        import urlparse

        q = urlparse.urlparse(signature[0])
        qs = urlparse.parse_qs(q.query,keep_blank_values=True)
        verify_params = dict()
        for k, v in qs.iteritems():
            verify_params[k] = v[0]
        ret = verify_request_common(consumers, url, method, headers, verify_params)
        self.assertTrue(ret)
