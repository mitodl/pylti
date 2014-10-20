# -*- coding: utf-8 -*-
"""
Test pylti/test_flask.py module
"""
from __future__ import absolute_import
import unittest
from pylti.common import LTIException, LTI_SESSION_KEY, LTIOAuthDataStore
from pylti.flask import lti
from flask import Flask, session, request
from pylti.tests.test_flask_app import state, app
import httpretty


class TestFlask(unittest.TestCase):
    consumers = {
        "__consumer_key__": {"secret": "__lti_secret__"}
    }


    def setUp(self):
        app.config['TESTING'] = True
        app.config['SERVER_NAME'] = 'localhost'
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SECRET_KEY'] = 'you-will-never-guess'
        app.config['PYLTI_CONFIG'] = {'consumers': self.consumers}
        app.config['PYLTI_URL_FIX'] = {
            "https://localhost:8000/": {
                "https://localhost:8000/": "http://localhost:8000/"
            }
        }
        self.app = app.test_client()
        self.reset_exception()

    def reset_exception(self):
        if state.has_key('exception'):
            del state['exception']
        self.assertFalse(state.has_key('exception'))

    def get_exception(self):
        return state['exception']['exception']


    def has_exception(self):
        return state.has_key('exception') and state['exception'].has_key('exception')

    def get_exception_as_string(self):
        return "{}".format(self.get_exception())

    def test_access_to_oauth_resource_unknown_protection(self):
        ret = self.app.get('/unknown_protection')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(), 'Unknown request type')

    def test_access_to_oauth_resource_without_authorization_any(self):
        ret = self.app.get('/any')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(), 'This page requires a valid oauth session or request')

    def test_access_to_oauth_resource_without_authorization_session(self):
        ret = self.app.get('/session')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(), 'Session expired or unavailable')

    def test_access_to_oauth_resource_without_authorization_initial_get(self):
        ret = self.app.get('/initial')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(), 'This page requires a valid oauth session or request')

    def test_access_to_oauth_resource_without_authorization_initial_post(self):
        ret = self.app.post('/initial')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(), 'This page requires a valid oauth session or request')


    def test_access_to_oauth_resource_in_session(self):
        ret = self.app.get('/setup_session')
        ret = self.app.get('/session')
        self.assertFalse(self.has_exception())

    def test_access_to_oauth_resource_in_session_with_close(self):
        self.app.get('/setup_session')
        self.app.get('/session')
        self.assertFalse(self.has_exception())
        self.app.get('/close_session')
        self.app.get('/session')
        self.assertTrue(self.has_exception())

    def test_access_to_oauth_resource(self):
        consumers = self.consumers
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(consumers, url)
        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())

    def generate_launch_request(self, consumers, url):
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
        signed_url = signature[0]
        new_url = signed_url[len('http://localhost'):]
        return new_url

    def test_access_to_oauth_resource_any(self):
        url = 'http://localhost/any?'
        new_url = self.generate_launch_request(self.consumers, url)
        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())


    def test_access_to_oauth_resource_invalid(self):
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(self.consumers, url)
        ret = self.app.get("{}&FAIL=TRUE".format(new_url))
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(), 'OAuth error: Please check your key and secret')


    def test_access_to_oauth_resource_invalid_after_session_setup(self):
        self.app.get('/setup_session')
        self.app.get('/session')
        self.assertFalse(self.has_exception())

        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(self.consumers, url)
        ret = self.app.get("{}&FAIL=TRUE".format(new_url))
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(), 'OAuth error: Please check your key and secret')

    @httpretty.activate
    def test_access_to_oauth_resource_post_grade(self):
        uri = 'https://edge.edx.org/courses/MITx/ODL_ENG/2014_T1/xblock/i4x:;_;_MITx;_ODL_ENG;_lti;_94173d3e79d145fd8ec2e83f15836ac8/handler_noauth/grade_handler'

        def request_callback(request, uri, headers):
            return (200, headers, "success")

        httpretty.register_uri(httpretty.POST, uri, body=request_callback)

        self.reset_exception()
        consumers = self.consumers
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(consumers, url)
        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())
        ret = self.app.get("/post_grade/1.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=True")
        ret = self.app.get("/post_grade/2.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=False")

    @httpretty.activate
    def test_access_to_oauth_resource_post_grade_fix_url(self):
        uri = 'https://localhost:8000/dev_stack'

        def request_callback(request, uri, headers):
            return (200, headers, "success")

        httpretty.register_uri(httpretty.POST, uri, body=request_callback)

        self.reset_exception()
        consumers = self.consumers
        url = 'http://localhost/initial?'

        method = 'GET'
        headers = dict()
        params = {'resource_link_id': u'edge.edx.org-i4x-MITx-ODL_ENG-lti-94173d3e79d145fd8ec2e83f15836ac8',
                  'user_id': u'008437924c9852377e8994829aaac7a1',
                  'roles': u'Instructor',
                  'lis_result_sourcedid': u'MITx/ODL_ENG/2014_T1:edge.edx.org-i4x-MITx-ODL_ENG-lti-94173d3e79d145fd8ec2e83f15836ac8:008437924c9852377e8994829aaac7a1',
                  'context_id': u'MITx/ODL_ENG/2014_T1',
                  'lti_version': u'LTI-1p0',
                  'launch_presentation_return_url': u'',
                  'lis_outcome_service_url': uri,
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
        signed_url = signature[0]
        new_url = signed_url[len('http://localhost'):]


        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())
        ret = self.app.get("/post_grade/1.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=True")
        ret = self.app.get("/post_grade/2.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=False")


# if __name__ == '__main__':
#     unittest.main()
