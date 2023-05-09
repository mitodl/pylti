# -*- coding: utf-8 -*-
"""
Common classes and methods for PyLTI module
"""

from __future__ import absolute_import

import logging
import json
import string
import time
from urllib.parse import urlencode

from oauthlib.oauth1 import RequestValidator, SignatureOnlyEndpoint
from oauthlib.oauth1.rfc5849 import CONTENT_TYPE_FORM_URLENCODED
from requests_oauthlib import OAuth1Session
from xml.etree import ElementTree as etree

log = logging.getLogger('pylti.common')  # pylint: disable=invalid-name

LTI_PROPERTY_LIST = [
    'oauth_consumer_key',
    'launch_presentation_return_url',
    'user_id',
    'oauth_nonce',
    'context_label',
    'context_id',
    'resource_link_title',
    'resource_link_id',
    'lis_person_contact_email_primary',
    'lis_person_contact_emailprimary',
    'lis_person_name_full',
    'lis_person_name_family',
    'lis_person_name_given',
    'lis_result_sourcedid',
    'lis_person_sourcedid',
    'launch_type',
    'lti_message',
    'lti_version',
    'roles',
    'lis_outcome_service_url'
]


LTI_ROLES = {
    u'staff': [u'Administrator', u'Instructor', ],
    u'instructor': [u'Instructor', ],
    u'administrator': [u'Administrator', ],
    u'student': [u'Student', u'Learner', ]
    # There is also a special role u'any' that ignores role check
}

LTI_SESSION_KEY = u'lti_authenticated'

LTI_REQUEST_TYPE = [u'any', u'initial', u'session']


def default_error(exception=None):
    """Render simple error page.  This should be overidden in applications."""
    # pylint: disable=unused-argument
    log.exception("There was an LTI communication error")
    return "There was an LTI communication error", 500


class LTIException(Exception):
    """
    Custom LTI exception for proper handling
    of LTI specific errors
    """
    pass


class LTINotInSessionException(LTIException):
    """
    Custom LTI exception for proper handling
    of LTI specific errors
    """
    pass


class LTIRoleException(LTIException):
    """
    Exception class for when LTI user doesn't have the
    right role.
    """
    pass


class LTIPostMessageException(LTIException):
    """
    Exception class for when LTI user doesn't have the
    right role.
    """
    pass


# https://oauthlib.readthedocs.io/en/latest/oauth1/validator.html
class LTIRequestValidator(RequestValidator):
    def __init__(self, consumers):
        self._consumers = consumers

    @property
    def enforce_ssl(self):
        # for backward-compatibility, we won't require SSL
        return False

    @property
    def safe_characters(self):
        # allowed characters in an LTI key
        return set(string.printable)

    @property
    def client_key_length(self):
        # some very loose guidelines on how long a key should be
        return 3, 1000

    @property
    def nonce_length(self):
        # some very loose guidelines on how long a nonce should be
        return 8, 1000

    def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
                                     request, request_token=None, access_token=None):
        """Validates that the timestamp is valid.

        # NOTE: Nonce reuse is **not** checked, though it should be by the OAuth spec.
        This implementation is attempting to match the python-oauth2 library, which
        does not record nonces or check them for reuse.

        :param client_key: The client/consumer key.
        :param timestamp: The ``oauth_timestamp`` parameter.
        :param nonce: The ``oauth_nonce`` parameter.
        :param request_token: Request token string, if any.
        :param access_token: Access token string, if any.
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :returns: True or False

        Per `Section 3.3`_ of the spec.

        "A nonce is a random string, uniquely generated by the client to allow
        the server to verify that a request has never been made before and
        helps prevent replay attacks when requests are made over a non-secure
        channel.  The nonce value MUST be unique across all requests with the
        same timestamp, client credentials, and token combinations."

        .. _`Section 3.3`: https://tools.ietf.org/html/rfc5849#section-3.3

        One of the first validation checks that will be made is for the validity
        of the nonce and timestamp, which are associated with a client key and
        possibly a token. If invalid then immediately fail the request
        by returning False. If the nonce/timestamp pair has been used before and
        you may just have detected a replay attack. Therefore it is an essential
        part of OAuth security that you not allow nonce/timestamp reuse.
        Note that this validation check is done before checking the validity of
        the client and token.::

           nonces_and_timestamps_database = [
              (u'foo', 1234567890, u'rannoMstrInghere', u'bar')
           ]

           def validate_timestamp_and_nonce(self, client_key, timestamp, nonce,
              request_token=None, access_token=None):

              return ((client_key, timestamp, nonce, request_token or access_token)
                       not in self.nonces_and_timestamps_database)
        """
        timestamp = int(timestamp)
        now = int(time.time())
        lapsed = now - timestamp
        if lapsed > self.timestamp_lifetime:
            return False

        return True

    def validate_client_key(self, client_key, request):
        """Validates that supplied client key is a registered and valid client.

        :param client_key: The client/consumer key.
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :returns: True or False
        """
        return client_key in self._consumers

    def get_client_secret(self, client_key, request):
        """Retrieves the client secret associated with the client key.

        :param client_key: The client/consumer key.
        :param request: OAuthlib request.
        :type request: oauthlib.common.Request
        :returns: The client secret as a string.
        """
        consumer = self._consumers.get(client_key, None)
        if consumer:
            return consumer.get('secret', None)
        else:
            return None


def _post_patched_request(consumers, lti_key, body,
                          url, method, content_type):
    """
    :param body: body of the call
    :param client: OAuth Client
    :param url: outcome url
    :return: response
    """
    try:
        consumer = consumers[lti_key]
    except ValueError:
        raise LTIException(f"Consumer {lti_key} not found in configured consumers.")

    secret = consumer.get('secret', None)
    lti_cert = consumer.get('cert', None)

    session = OAuth1Session(lti_key, client_secret=secret)
    response = session.request(method, url, data=body, headers={'Content-Type': content_type}, cert=lti_cert)

    log.debug("key %s", lti_key)
    log.debug("secret %s", secret)
    log.debug("url %s", url)
    log.debug("status %s", response.status_code)
    log.debug("content %s", format(response.content))

    return response, response.content


def post_message(consumers, lti_key, url, body):
    """
        Posts a signed message to LTI consumer

    :param consumers: consumers from config
    :param lti_key: key to find appropriate consumer
    :param url: post url
    :param body: xml body
    :return: success
    """
    content_type = 'application/xml'
    method = 'POST'
    (_, content) = _post_patched_request(
        consumers,
        lti_key,
        body,
        url,
        method,
        content_type,
    )

    is_success = b"<imsx_codeMajor>success</imsx_codeMajor>" in content
    log.debug("is success %s", is_success)
    return is_success


def post_message2(consumers, lti_key, url, body,
                  method='POST', content_type='application/xml'):
    """
        Posts a signed message to LTI consumer using LTI 2.0 format

    :param: consumers: consumers from config
    :param: lti_key: key to find appropriate consumer
    :param: url: post url
    :param: body: xml body
    :return: success
    """
    # pylint: disable=too-many-arguments
    (response, _) = _post_patched_request(
        consumers,
        lti_key,
        body,
        url,
        method,
        content_type,
    )

    is_success = response.status_code == 200
    log.debug("is success %s", is_success)

    return is_success


def verify_request_common(consumers, url, method, headers, params):
    """
    Verifies that request is valid

    :param consumers: consumers from config file
    :param url: request url
    :param method: request method
    :param headers: request headers
    :param params: request params
    :return: is request valid
    """
    log.debug("consumers %s", consumers)
    log.debug("url %s", url)
    log.debug("method %s", method)
    log.debug("headers %s", headers)
    log.debug("params %s", params)

    # Check header for SSL before selecting the url
    if (
        headers.get(
            "X-Forwarded-Proto",
            headers.get("HTTP_X_FORWARDED_PROTO", "http"),
        ) == "https"
    ):
        url = url.replace('http:', 'https:', 1)

    headers = dict(headers)
    body = None
    if params:
        params = dict(params)
        if method == "POST":
            headers['Content-Type'] = headers.get('Content-Type', CONTENT_TYPE_FORM_URLENCODED)
            body = urlencode(params, True)
        else:
            url = f"{url}?{urlencode(params, True)}"
            body = None

    validator = LTIRequestValidator(consumers)
    endpoint = SignatureOnlyEndpoint(validator)
    valid, _ = endpoint.validate_request(
        url,
        method,
        body=body,
        headers=headers)
    if not valid:
        raise LTIException("OAuth error: Please check your key and secret")

    return True


def generate_request_xml(message_identifier_id, operation,
                         lis_result_sourcedid, score):
    # pylint: disable=too-many-locals
    """
    Generates LTI 1.1 XML for posting result to LTI consumer.

    :param message_identifier_id:
    :param operation:
    :param lis_result_sourcedid:
    :param score:
    :return: XML string
    """
    root = etree.Element(u'imsx_POXEnvelopeRequest',
                         xmlns=u'http://www.imsglobal.org/services/'
                               u'ltiv1p1/xsd/imsoms_v1p0')

    header = etree.SubElement(root, 'imsx_POXHeader')
    header_info = etree.SubElement(header, 'imsx_POXRequestHeaderInfo')
    version = etree.SubElement(header_info, 'imsx_version')
    version.text = 'V1.0'
    message_identifier = etree.SubElement(header_info,
                                          'imsx_messageIdentifier')
    message_identifier.text = message_identifier_id
    body = etree.SubElement(root, 'imsx_POXBody')
    xml_request = etree.SubElement(body, '%s%s' % (operation, 'Request'))
    record = etree.SubElement(xml_request, 'resultRecord')

    guid = etree.SubElement(record, 'sourcedGUID')

    sourcedid = etree.SubElement(guid, 'sourcedId')
    sourcedid.text = lis_result_sourcedid
    if score is not None:
        result = etree.SubElement(record, 'result')
        result_score = etree.SubElement(result, 'resultScore')
        language = etree.SubElement(result_score, 'language')
        language.text = 'en'
        text_string = etree.SubElement(result_score, 'textString')
        text_string.text = score.__str__()
    ret = "<?xml version='1.0' encoding='utf-8'?>\n{}".format(
        etree.tostring(root, encoding='utf-8').decode('utf-8'))

    log.debug("XML Response: \n%s", ret)
    return ret


class LTIBase(object):
    """
    LTI Object represents abstraction of current LTI session. It provides
    callback methods and methods that allow developer to inspect
    LTI basic-launch-request.

    This object is instantiated by @lti wrapper.
    """
    def __init__(self, lti_args, lti_kwargs):
        self.lti_args = lti_args
        self.lti_kwargs = lti_kwargs
        self.nickname = self.name

    @property
    def name(self):  # pylint: disable=no-self-use
        """
        Name returns user's name or user's email or user_id
        :return: best guess of name to use to greet user
        """
        if 'lis_person_sourcedid' in self.session:
            return self.session['lis_person_sourcedid']
        elif 'lis_person_contact_email_primary' in self.session:
            return self.session['lis_person_contact_email_primary']
        elif 'user_id' in self.session:
            return self.session['user_id']
        else:
            return ''

    def verify(self):
        """
        Verify if LTI request is valid, validation
        depends on @lti wrapper arguments

        :raises: LTIException
        """
        log.debug('verify request=%s', self.lti_kwargs.get('request'))
        if self.lti_kwargs.get('request') == 'session':
            self._verify_session()
        elif self.lti_kwargs.get('request') == 'initial':
            self.verify_request()
        elif self.lti_kwargs.get('request') == 'any':
            self._verify_any()
        else:
            raise LTIException("Unknown request type")
        return True

    @property
    def user_id(self):  # pylint: disable=no-self-use
        """
        Returns user_id as provided by LTI

        :return: user_id
        """
        return self.session['user_id']

    @property
    def key(self):  # pylint: disable=no-self-use
        """
        OAuth Consumer Key
        :return: key
        """
        return self.session['oauth_consumer_key']

    @staticmethod
    def message_identifier_id():
        """
        Message identifier to use for XML callback

        :return: non-empty string
        """
        return "edX_fix"

    @property
    def lis_result_sourcedid(self):  # pylint: disable=no-self-use
        """
        lis_result_sourcedid to use for XML callback

        :return: LTI lis_result_sourcedid
        """
        return self.session['lis_result_sourcedid']

    @property
    def role(self):  # pylint: disable=no-self-use
        """
        LTI roles

        :return: roles
        """
        return self.session.get('roles')

    @staticmethod
    def is_role(self, role):
        """
        Verify if user is in role

        :param: role: role to verify against
        :return: if user is in role
        :exception: LTIException if role is unknown
        """
        log.debug("is_role %s", role)
        roles = self.session['roles'].split(',')
        if role in LTI_ROLES:
            role_list = LTI_ROLES[role]
            # find the intersection of the roles
            roles = set(role_list) & set(roles)
            is_user_role_there = len(roles) >= 1
            log.debug(
                "is_role roles_list=%s role=%s in list=%s", role_list,
                roles, is_user_role_there
            )
            return is_user_role_there
        else:
            raise LTIException("Unknown role {}.".format(role))

    def _check_role(self):
        """
        Check that user is in role specified as wrapper attribute

        :exception: LTIRoleException if user is not in roles
        """
        role = u'any'
        if 'role' in self.lti_kwargs:
            role = self.lti_kwargs['role']
        log.debug(
            "check_role lti_role=%s decorator_role=%s", self.role, role
        )
        if not (role == u'any' or self.is_role(self, role)):
            raise LTIRoleException('Not authorized.')

    def post_grade(self, grade):
        """
        Post grade to LTI consumer using XML

        :param: grade: 0 <= grade <= 1
        :return: True if post successful and grade valid
        :exception: LTIPostMessageException if call failed
        """
        message_identifier_id = self.message_identifier_id()
        operation = 'replaceResult'
        lis_result_sourcedid = self.lis_result_sourcedid
        # # edX devbox fix
        score = float(grade)
        if 0 <= score <= 1.0:
            xml = generate_request_xml(
                message_identifier_id, operation, lis_result_sourcedid,
                score)
            ret = post_message(self._consumers(), self.key,
                               self.response_url, xml)
            if not ret:
                raise LTIPostMessageException("Post Message Failed")
            return True

        return False

    def post_grade2(self, grade, user=None, comment=''):
        """
        Post grade to LTI consumer using REST/JSON
        URL munging will is related to:
        https://openedx.atlassian.net/browse/PLAT-281

        :param: grade: 0 <= grade <= 1
        :return: True if post successful and grade valid
        :exception: LTIPostMessageException if call failed
        """
        content_type = 'application/vnd.ims.lis.v2.result+json'
        if user is None:
            user = self.user_id
        lti2_url = self.response_url.replace(
            "/grade_handler",
            "/lti_2_0_result_rest_handler/user/{}".format(user))
        score = float(grade)
        if 0 <= score <= 1.0:
            body = json.dumps({
                "@context": "http://purl.imsglobal.org/ctx/lis/v2/Result",
                "@type": "Result",
                "resultScore": score,
                "comment": comment
            })
            ret = post_message2(self._consumers(), self.key, lti2_url, body,
                                method='PUT',
                                content_type=content_type)
            if not ret:
                raise LTIPostMessageException("Post Message Failed")
            return True

        return False
