# -*- coding: utf-8 -*-
"""
Common classes and methods for PyLTI module
"""

from __future__ import absolute_import
import logging

import oauth.oauth as oauth
import oauthlib.oauth1
from lxml import etree
import requests

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
    u'student': [u'Student', ],
    u'any': [u'Administrator', u'Instructor', u'Student', ],
}

LTI_SESSION_KEY = u'lti_authenticated'

LTI_REQUEST_TYPE = [u'any', u'initial', u'session']

class LTIOAuthDataStore(oauth.OAuthDataStore):
    """
    Largely taken from reference implementation
    for app engine at https://code.google.com/p/ims-dev/
    """

    def __init__(self, consumers):
        """
        Create OAuth store
        """
        oauth.OAuthDataStore.__init__(self)
        self.consumers = consumers

    def lookup_consumer(self, key):
        """
        Search through keys
        """
        if not self.consumers:
            log.critical(("No consumers defined in settings."
                          "Have you created a configuration file?"))
            return None

        consumer = self.consumers.get(key)
        if not consumer:
            log.info("Did not find consumer, using key: %s ", key)
            return None

        secret = consumer.get('secret', None)
        if not secret:
            log.critical(('Consumer %s, is missing secret'
                          'in settings file, and needs correction.'), key)
            return None
        return oauth.OAuthConsumer(key, secret)

    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        """
        Lookup nonce should check if nonce was already used
        by this consumer in the past.
        Reusing nonce is bad: http://cwe.mitre.org/data/definitions/323.html
        Not implemented.
        """
        return None


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


def post_message(consumers, lti_key, url, body):
    """
        Posts a signed message to LTI consumer
    :param consumers: consumers from config
    :param lti_key: key to find appropriate consumer
    :param url: post url
    :param body: xml body
    :return: success
    """
    oauth_store = LTIOAuthDataStore(consumers)
    oauth_server = oauth.OAuthServer(oauth_store)
    oauth_server.add_signature_method(oauth.OAuthSignatureMethod_HMAC_SHA1())
    lti_consumer = oauth_store.lookup_consumer(lti_key)
    secret = lti_consumer.secret

    client = oauthlib.oauth1.Client(lti_key,
                                    client_secret=secret,
                                    signature_method=oauthlib.oauth1.
                                    SIGNATURE_HMAC,
                                    signature_type=oauthlib.oauth1.
                                    SIGNATURE_TYPE_QUERY)

    (url, headers, oauthbody) = client.sign(url, 'POST', body,
                                            headers={'Content-Type':
                                                     'application/xml'})

    response = requests.post(url=url, data=oauthbody, headers=headers)
    log.debug("key {}".format(lti_key))
    log.debug("secret {}".format(secret))
    log.debug("url {}".format(url))
    log.debug(body)
    log.debug(response.text)
    log.debug(response.ok)
    return response.ok


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

    log.debug("consumers {}".format(consumers))
    log.debug("url {}".format(url))
    log.debug("method {}".format(method))
    log.debug("headers {}".format(headers))
    log.debug("params {}".format(params))
    oauth_store = LTIOAuthDataStore(consumers)
    oauth_server = oauth.OAuthServer(oauth_store)
    oauth_server.add_signature_method(
        oauth.OAuthSignatureMethod_PLAINTEXT())
    oauth_server.add_signature_method(
        oauth.OAuthSignatureMethod_HMAC_SHA1())

    # Check header for SSL before selecting the url
    if headers.get('X-Forwarded-Proto', 'http') == 'https':
        url = url.replace('http', 'https', 1)

    oauth_request = oauth.OAuthRequest.from_request(
        method,
        url,
        headers=dict(headers),
        parameters=params
    )

    if not oauth_request:
        log.info('Received non oauth request on oauth protected page')
        raise LTIException('This page requires a valid oauth session '
                           'or request')
    try:
        # pylint: disable=protected-access
        consumer = oauth_server._get_consumer(oauth_request)
        oauth_server._check_signature(oauth_request, consumer, None)
    except oauth.OAuthError:
        # Rethrow our own for nice error handling (don't print
        # error message as it will contain the key
        raise LTIException("OAuth error: Please check your key and secret")

    return True


def generate_request_xml(message_identifier_id, operation,
                         lis_result_sourcedid, score):
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
    log.debug("XML Response: \n{}".format(
        etree.tostring(root, xml_declaration=True, encoding='utf-8')))
    return etree.tostring(root, xml_declaration=True, encoding='utf-8')
