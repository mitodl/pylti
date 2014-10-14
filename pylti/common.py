from __future__ import absolute_import

"""
Classes to handle oauth portion of LTI
"""
# pylint: disable=C0103
import logging
# pylint: disable=C0103
from functools import wraps

import oauth2
from flask import Flask, session, request

import oauth.oauth as oauth

log = logging.getLogger('pylti.common')


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

    def lookup_token(self, oauth_consumer, token_type, token):
        """We don't do request_tokens"""
        # pylint: disable=W0613
        return oauth.OAuthToken(None, None)  # pragma: no cover

    def lookup_nonce(self, oauth_consumer, oauth_token, nonce):
        """Trust all nonces"""
        return None  # pragma: no cover

    def fetch_request_token(self, oauth_consumer, oauth_callback):
        """We don't do request_tokens"""
        return None  # pragma: no cover

    def fetch_access_token(self, oauth_consumer, oauth_token, oauth_verifier):
        """We don't do request_tokens"""
        return None  # pragma: no cover

    def authorize_request_token(self, oauth_token, user):
        """We don't do request_tokens"""
        return None  # pragma: no cover


"""
Utility support functions
"""


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


"""
Decorators to handle LTI session management,
authentication, etc.
"""

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

LTI_STAFF_ROLES = ['Instructor', 'Administrator', ]

LTI_SESSION_KEY = 'lti_authenticated'


def post_message(consumers, lti_key, url, body):
    oauth_store = LTIOAuthDataStore(consumers)
    oauth_server = oauth.OAuthServer(oauth_store)
    oauth_server.add_signature_method(oauth.OAuthSignatureMethod_HMAC_SHA1())
    c = oauth_store.lookup_consumer(lti_key)
    secret = c.secret
    consumer = oauth2.Consumer(key=lti_key, secret=secret)
    client = oauth2.Client(consumer)
    # monkey_patch_headers ensures that Authorization header is NOT lower cased
    monkey_patch_headers = True
    monkey_patch_function = None
    if monkey_patch_headers:
        import httplib2

        http = httplib2.Http
        normalize = http._normalize_headers

        def my_normalize(self, headers):
            ret = normalize(self, headers)
            if ret.has_key('authorization'):
                ret['Authorization'] = ret.pop('authorization')
            log.debug("headers")
            log.debug(headers)
            return ret

        http._normalize_headers = my_normalize
        monkey_patch_function = normalize

    response, content = client.request(
        url,
        'POST',
        body=body,
        headers={'Content-Type': 'application/xml'})

    if monkey_patch_headers and monkey_patch_function:
        import httplib2

        http = httplib2.Http
        http._normalize_headers = monkey_patch_function
    log.debug("key {}".format(lti_key))
    log.debug("secret {}".format(secret))
    log.debug("url {}".format(url))
    log.debug(body)
    log.debug(response)
    # log.debug(content)

    pass


def verify_request_common(consumers, url, method, headers, params):
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
        consumer = oauth_server._get_consumer(oauth_request)
        oauth_server._check_signature(oauth_request, consumer, None)
    except oauth.OAuthError as err:
        # Rethrow our own for nice error handling (don't print
        # error message as it will contain the key
        log.info(err.message)
        raise LTIException("OAuth error: Please check your key and secret")

    return True


def lti_staff_required(func):
    """
    Decorator to make sure that person is a
    member of one of the course staff roles
    before allowing them to the view. Requires that
    lti_authentication has occurred
    """

    @wraps(func)
    def decorator(*args, **kwargs):
        """
        Check session['role'] against known list of course staff
        roles and raise if it isn't in that set.
        """
        log.debug(session)
        role = session.get('roles', None)
        if not role:
            raise LTIRoleException(
                'User does not have a role. One is required'
            )
        if role not in LTI_STAFF_ROLES:
            raise LTIRoleException(
                'You are not in a staff level role. Access is restricted '
                'to course staff.'
            )
        return func(*args, **kwargs)

    return decorator