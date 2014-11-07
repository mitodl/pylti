# -*- coding: utf-8 -*-
"""
Test pylti/test_flask.py module
"""
from __future__ import absolute_import
import unittest
import urllib

import httpretty
import oauthlib.oauth1

from pylti.common import LTIException
from pylti.tests.test_flask_app import app_exception, app


class TestFlask(unittest.TestCase):
    """
    Consumers
    """
    consumers = {
        "__consumer_key__": {"secret": "__lti_secret__"}
    }

    """
    Valid XML response from LTI 1.0 consumer
    """
    expected_response = """<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeResponse xmlns = "http://www.imsglobal.org/services/ltiv1p1\
/xsd/imsoms_v1p0">
    <imsx_POXHeader>
        <imsx_POXResponseHeaderInfo>
            <imsx_version>V1.0</imsx_version>
            <imsx_messageIdentifier>edX_fix</imsx_messageIdentifier>
            <imsx_statusInfo>
                <imsx_codeMajor>success</imsx_codeMajor>
                <imsx_severity>status</imsx_severity>
                <imsx_description>Score for StarX/StarX_DEMO/201X_StarX:\
edge.edx.org-i4x-StarX-StarX_DEMO-lti-40559041895b4065b2818c23b9cd9da8\
:18b71d3c46cb4dbe66a7c950d88e78ec is now 0.0</imsx_description>
                <imsx_messageRefIdentifier>
                </imsx_messageRefIdentifier>
            </imsx_statusInfo>
        </imsx_POXResponseHeaderInfo>
    </imsx_POXHeader>
    <imsx_POXBody><replaceResultResponse/></imsx_POXBody>
</imsx_POXEnvelopeResponse>
        """

    def setUp(self):
        """
        Setting up app config
        """
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
        app_exception.reset()

    def get_exception(self):
        """
        Returns exception raised by PyLTI
        :return: exception
        """
        return app_exception.get()

    def has_exception(self):
        """
        Check if PyLTI raised exception
        :return: is exception raised
        """
        return app_exception.get() is not None

    def get_exception_as_string(self):
        """
        Return text of the exception raised by LTI
        :return: text
        """
        return "{}".format(self.get_exception())

    def test_access_to_oauth_resource_unknown_protection(self):
        """
        Invalid LTI request scope
        """
        self.app.get('/unknown_protection')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(),
                         'Unknown request type')

    def test_access_to_oauth_resource_without_authorization_any(self):
        """
        Accessing LTI without establishing session
        """
        self.app.get('/any')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(),
                         'This page requires a valid oauth session or request')

    def test_access_to_oauth_resource_without_authorization_session(self):
        """
        Accessing LTI session scope before session established
        """
        self.app.get('/session')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(),
                         'Session expired or unavailable')

    def test_access_to_oauth_resource_without_authorization_initial_get(self):
        """
        Accessing LTI without basic-lti-launch-request parameters as GET
        """
        self.app.get('/initial')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(),
                         'This page requires a valid oauth session or request')

    def test_access_to_oauth_resource_without_authorization_initial_post(self):
        """
        Accessing LTI without basic-lti-launch-request parameters as POST
        """
        self.app.post('/initial')
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(),
                         'This page requires a valid oauth session or request')

    def test_access_to_oauth_resource_in_session(self):
        """
        Accessing LTI after session established
        """
        self.app.get('/setup_session')

        self.app.get('/session')
        self.assertFalse(self.has_exception())

    def test_access_to_oauth_resource_in_session_with_close(self):
        """
        Accessing LTI after session closed
        """
        self.app.get('/setup_session')

        self.app.get('/session')

        self.assertFalse(self.has_exception())

        self.app.get('/close_session')

        self.app.get('/session')

        self.assertTrue(self.has_exception())

    def test_access_to_oauth_resource(self):
        """
        Accessing oauth_resource
        """
        consumers = self.consumers
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(consumers, url)

        self.app.get(new_url)
        self.assertFalse(self.has_exception())

    def test_access_to_oauth_resource_name_passed(self):
        """
        Check that name is returned if passed via initial request
        """
        consumers = self.consumers
        url = 'http://localhost/name?'
        add_params = {u'lis_person_sourcedid': u'person'}
        new_url = self.generate_launch_request(consumers, url,
                                               add_params=add_params)

        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, u'person')

    def test_access_to_oauth_resource_email_passed(self):
        """
        Check that email is returned if passed via initial request
        """
        consumers = self.consumers
        url = 'http://localhost/name?'
        add_params = {u'lis_person_contact_email_primary': u'email@email.com'}
        new_url = self.generate_launch_request(consumers, url,
                                               add_params=add_params)

        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, u'email@email.com')

    def test_access_to_oauth_resource_name_and_email_passed(self):
        """
        Check that name is returned if both email and name passed
        """
        consumers = self.consumers
        url = 'http://localhost/name?'
        add_params = {u'lis_person_sourcedid': u'person',
                      u'lis_person_contact_email_primary': u'email@email.com'}
        new_url = self.generate_launch_request(consumers, url,
                                               add_params=add_params)

        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, u'person')

    def test_access_to_oauth_resource_staff_only_as_student(self):
        """
        Deny access if user not in role
        """
        consumers = self.consumers
        url = 'http://localhost/initial_staff?'
        new_url = self.generate_launch_request(consumers, url,
                                               roles='Student')

        self.app.get(new_url)
        self.assertTrue(self.has_exception())

    def test_access_to_oauth_resource_staff_only_as_administrator(self):
        """
        Allow access if user in role
        """
        consumers = self.consumers
        url = 'http://localhost/initial_staff?'
        new_url = self.generate_launch_request(consumers, url,
                                               roles='Administrator')

        self.app.get(new_url)
        self.assertFalse(self.has_exception())

    def test_access_to_oauth_resource_staff_only_as_unknown_role(self):
        """
        Deny access if role not defined
        """
        consumers = self.consumers
        url = 'http://localhost/initial_unknown?'
        new_url = self.generate_launch_request(consumers, url,
                                               roles='Administrator')

        self.app.get(new_url)
        self.assertTrue(self.has_exception())

    def generate_launch_request(self, consumers, url,
                                lit_outcome_service_url=None,
                                roles=u'Instructor',
                                add_params=None):
        """
        Generate valid basic-lti-launch-request request with options
        :param consumers: consumer map
        :param url: URL to sign
        :param lit_outcome_service_url: LTI callback
        :param roles: LTI role
        :return: signed request
        """
        params = {'resource_link_id': u'edge.edx.org-i4x-MITx-ODL_ENG-lti-'
                                      u'94173d3e79d145fd8ec2e83f15836ac8',
                  'user_id': u'008437924c9852377e8994829aaac7a1',
                  'roles': roles,
                  'lis_result_sourcedid': u'MITx/ODL_ENG/2014_T1:'
                                          u'edge.edx.org-i4x-MITx-ODL_ENG-lti-'
                                          u'94173d3e79d145fd8ec2e83f15836ac8:'
                                          u'008437924c9852377e8994829aaac7a1',
                  'context_id': u'MITx/ODL_ENG/2014_T1',
                  'lti_version': u'LTI-1p0',
                  'launch_presentation_return_url': u'',
                  'lis_outcome_service_url': (lit_outcome_service_url
                                              or u'https://edge.edx.org/'
                                                 u'courses/MITx/ODL_ENG/'
                                                 u'2014_T1/xblock/i4x:;_;'
                                                 u'_MITx;_ODL_ENG;_lti;'
                                                 u'_94173d3e79d145fd8ec2e'
                                                 u'83f15836ac8'
                                                 u'/handler_noauth/'
                                                 u'grade_handler'),
                  'lti_message_type': u'basic-lti-launch-request',
                  }
        if add_params is not None:
            params.update(add_params)

        urlparams = urllib.urlencode(params)

        client = oauthlib.oauth1.Client('__consumer_key__',
                                        client_secret='__lti_secret__',
                                        signature_method=oauthlib.oauth1.
                                        SIGNATURE_HMAC,
                                        signature_type=oauthlib.oauth1.
                                        SIGNATURE_TYPE_QUERY)
        signature = client.sign("{}{}".format(url, urlparams))
        signed_url = signature[0]
        new_url = signed_url[len('http://localhost'):]
        return new_url

    def test_access_to_oauth_resource_any(self):
        """
        Test access to LTI protected resources
        """
        url = 'http://localhost/any?'
        new_url = self.generate_launch_request(self.consumers, url)
        self.app.get(new_url)
        self.assertFalse(self.has_exception())

    def test_access_to_oauth_resource_invalid(self):
        """
        Deny access to LTI protected resources
        on man in the middle attack
        """
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(self.consumers, url)

        self.app.get("{}&FAIL=TRUE".format(new_url))
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(),
                         'OAuth error: Please check your key and secret')

    def test_access_to_oauth_resource_invalid_after_session_setup(self):
        """
        Remove browser session on man in the middle attach
        """
        self.app.get('/setup_session')
        self.app.get('/session')
        self.assertFalse(self.has_exception())

        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(self.consumers, url)

        self.app.get("{}&FAIL=TRUE".format(new_url))
        self.assertTrue(self.has_exception())
        self.assertIsInstance(self.get_exception(), LTIException)
        self.assertEqual(self.get_exception_as_string(),
                         'OAuth error: Please check your key and secret')

    @httpretty.activate
    def test_access_to_oauth_resource_post_grade(self):
        """
        Check post_grade functionality
        """
        uri = (u'https://edge.edx.org/courses/MITx/ODL_ENG/2014_T1/xblock/'
               u'i4x:;_;_MITx;_ODL_ENG;_lti;'
               u'_94173d3e79d145fd8ec2e83f15836ac8/handler_noauth'
               u'/grade_handler')

        def request_callback(request, cburi, headers):
            return 200, headers, self.expected_response

        httpretty.register_uri(httpretty.POST, uri, body=request_callback)

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
    def test_access_to_oauth_resource_post_grade_fail(self):
        """
        Check post_grade functionality fails on invalid response
        """
        uri = (u'https://edge.edx.org/courses/MITx/ODL_ENG/2014_T1/xblock/'
               u'i4x:;_;_MITx;_ODL_ENG;_lti;'
               u'_94173d3e79d145fd8ec2e83f15836ac8/handler_noauth'
               u'/grade_handler')

        def request_callback(request, cburi, headers):
            return 200, headers, "wrong_response"

        httpretty.register_uri(httpretty.POST, uri, body=request_callback)

        consumers = self.consumers
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(consumers, url)
        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())

        ret = self.app.get("/post_grade/1.0")
        self.assertTrue(self.has_exception())
        self.assertEqual(ret.data, "error")

    @httpretty.activate
    def test_access_to_oauth_resource_post_grade_fix_url(self):
        """
        Make sure URL remap works for edX vagrant stack
        """
        uri = 'https://localhost:8000/dev_stack'

        def request_callback(request, cburi, headers):
            return 200, headers, self.expected_response

        httpretty.register_uri(httpretty.POST, uri, body=request_callback)

        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(self.consumers, url,
                                               lit_outcome_service_url=uri)

        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())

        ret = self.app.get("/post_grade/1.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=True")

        ret = self.app.get("/post_grade/2.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=False")

    @httpretty.activate
    def test_access_to_oauth_resource_post_grade2(self):
        """
        Check post_grade edX LTI2 functionality
        """

        uri = (u'https://edge.edx.org/courses/MITx/ODL_ENG/2014_T1/xblock/'
               u'i4x:;_;_MITx;_ODL_ENG;_lti;'
               u'_94173d3e79d145fd8ec2e83f15836ac8/handler_noauth'
               u'/lti_2_0_result_rest_handler/user/'
               u'008437924c9852377e8994829aaac7a1')

        def request_callback(request, cburi, headers):
            return 200, headers, self.expected_response

        httpretty.register_uri(httpretty.PUT, uri, body=request_callback)

        consumers = self.consumers
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(consumers, url)

        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())

        ret = self.app.get("/post_grade2/1.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=True")

        ret = self.app.get("/post_grade2/2.0")
        self.assertFalse(self.has_exception())
        self.assertEqual(ret.data, "grade=False")

    @httpretty.activate
    def test_access_to_oauth_resource_post_grade2_fail(self):
        """
        Check post_grade edX LTI2 functionality
        """

        uri = (u'https://edge.edx.org/courses/MITx/ODL_ENG/2014_T1/xblock/'
               u'i4x:;_;_MITx;_ODL_ENG;_lti;'
               u'_94173d3e79d145fd8ec2e83f15836ac8/handler_noauth'
               u'/lti_2_0_result_rest_handler/user/'
               u'008437924c9852377e8994829aaac7a1')

        def request_callback(request, cburi, headers):
            return 400, headers, self.expected_response

        httpretty.register_uri(httpretty.PUT, uri, body=request_callback)

        consumers = self.consumers
        url = 'http://localhost/initial?'
        new_url = self.generate_launch_request(consumers, url)
        ret = self.app.get(new_url)
        self.assertFalse(self.has_exception())
        ret = self.app.get("/post_grade2/1.0")
        self.assertTrue(self.has_exception())
        self.assertEqual(ret.data, "error")
