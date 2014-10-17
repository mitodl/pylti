# -*- coding: utf-8 -*-
"""
Test pylti/common.py module
"""
from pylti.common import LTIOAuthDataStore, verify_request_common, LTIException, post_message, generate_request_xml
import unittest
from oauth import oauth
import httpretty


class TestCommon(unittest.TestCase):

    def test_LTIOAuthDataStore(self):
        consumers = {
            "key1": {"secret": "secret1"},
            "key2": {"secret": "secret2"},
            "key3": {"secret": "secret3"},
            "keyNS": {"test":"mytest"}
        }
        store = LTIOAuthDataStore(consumers)
        self.assertEqual(store.lookup_consumer("key1").secret, "secret1")
        self.assertEqual(store.lookup_consumer("key2").secret, "secret2")
        self.assertEqual(store.lookup_consumer("key3").secret, "secret3")
        self.assertIsNone(store.lookup_consumer("key4"))
        self.assertIsNone(store.lookup_consumer("keyNS"))

    def test_LTIOAuthDataStore_NoConsumers(self):
        store = LTIOAuthDataStore(None)
        self.assertIsNone(store.lookup_consumer("key1"))


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

    def test_verify_request_common_via_proxy(self):
        consumers = {
            "__consumer_key__": {"secret": "__lti_secret__"}
        }
        url = 'http://localhost:5000/?'
        orig_url = 'https://localhost:5000/?'
        method = 'GET'
        headers = dict()
        headers['X-Forwarded-Proto'] = 'https'
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
        signature = client.sign("{}{}".format(orig_url, urlparams))
        import urlparse

        q = urlparse.urlparse(signature[0])
        qs = urlparse.parse_qs(q.query,keep_blank_values=True)
        verify_params = dict()
        for k, v in qs.iteritems():
            verify_params[k] = v[0]
        ret = verify_request_common(consumers, url, method, headers, verify_params)
        self.assertTrue(ret)

    def test_verify_request_common_no_auth_fields(self):
        consumers = {
            "__consumer_key__": {"secret": "__lti_secret__"}
        }
        url = 'http://localhost:5000/?'
        orig_url = 'https://localhost:5000/?'
        method = 'GET'
        headers = dict()
        headers['X-Forwarded-Proto'] = 'https'
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

        ret = False
        try:
            ret = verify_request_common(consumers, url, method, headers, params)
        except LTIException as e:
            self.assertTrue(True)
        self.assertFalse(ret)

    def test_verify_request_common_no_params(self):
        consumers = {
            "__consumer_key__": {"secret": "__lti_secret__"}
        }
        url = 'http://localhost:5000/?'
        orig_url = 'https://localhost:5000/?'
        method = 'GET'
        headers = dict()
        headers['X-Forwarded-Proto'] = 'https'
        params = dict()
        ret = False
        try:
            ret = verify_request_common(consumers, url, method, headers, params)
        except LTIException as e:
            self.assertTrue(True)
        self.assertFalse(ret)


    @httpretty.activate
    def test_post_response(self):
        uri = 'https://edge.edx.org/courses/MITx/ODL_ENG/2014_T1/xblock/i4x:;_;_MITx;_ODL_ENG;_lti;_94173d3e79d145fd8ec2e83f15836ac8/handler_noauth/grade_handler'
        def request_callback(request,uri,headers):
            return (200,headers,"success")

        httpretty.register_uri(httpretty.POST, uri, body=request_callback)
        consumers = {
            "__consumer_key__": {"secret": "__lti_secret__"}
        }
        body = 'THIS_IS_RESPONSE'
        post_message(consumers,"__consumer_key__", uri, body)

    def test_generate_xml(self):
        xml = generate_request_xml('message_identifier_id','operation','lis_result_sourcedid','score')
        self.assertEqual(xml,"""<?xml version='1.0' encoding='utf-8'?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"><imsx_POXHeader><imsx_POXRequestHeaderInfo><imsx_version>V1.0</imsx_version><imsx_messageIdentifier>message_identifier_id</imsx_messageIdentifier></imsx_POXRequestHeaderInfo></imsx_POXHeader><imsx_POXBody><operationRequest><resultRecord><sourcedGUID><sourcedId>lis_result_sourcedid</sourcedId></sourcedGUID><result><resultScore><language>en</language><textString>score</textString></resultScore></result></resultRecord></operationRequest></imsx_POXBody></imsx_POXEnvelopeRequest>""");
        xml = generate_request_xml('message_identifier_id','operation','lis_result_sourcedid',None)
        self.assertEqual(xml,"""<?xml version='1.0' encoding='utf-8'?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0"><imsx_POXHeader><imsx_POXRequestHeaderInfo><imsx_version>V1.0</imsx_version><imsx_messageIdentifier>message_identifier_id</imsx_messageIdentifier></imsx_POXRequestHeaderInfo></imsx_POXHeader><imsx_POXBody><operationRequest><resultRecord><sourcedGUID><sourcedId>lis_result_sourcedid</sourcedId></sourcedGUID></resultRecord></operationRequest></imsx_POXBody></imsx_POXEnvelopeRequest>""")

# if __name__ == '__main__':
#     unittest.main()