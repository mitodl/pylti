# -*- coding: utf-8 -*-
"""
    PyLTI decorator implementation for chalice framework
"""
from __future__ import absolute_import
from functools import wraps
import logging
import os
from chalice import Chalice

try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs

try:
    from urllib.parse import urlunparse
except ImportError:
    from urlparse import urlunparse

from .common import (
    LTI_SESSION_KEY,
    LTI_PROPERTY_LIST,
    verify_request_common,
    default_error,
    LTIException,
    LTIBase
)

logging.basicConfig()
log = logging.getLogger('pylti.chalice')  # pylint: disable=invalid-name


class LTI(LTIBase):
    """
    LTI Object represents abstraction of current LTI session. It provides
    callback methods and methods that allow developer to inspect
    LTI basic-launch-request.

    This object is instantiated by @lti wrapper.
    """

    def __init__(self, lti_args, lti_kwargs):
        # Chalice does not support sessions. Yet, we want the experiance
        # to be the same as Flask. Therefore, use a simple dictionary
        # to keep session variables for the length of this request.
        self.session = {}
        LTIBase.__init__(self, lti_args, lti_kwargs)

    def _consumers(self):
        """
        Gets consumers from Lambda environment variables prefixed with
        CONSUMER_KEY_SECRET_. For example, given a consumer key of foo
        and a shared secret of bar, you should have an environment
        variable CONSUMER_KEY_SECRET_foo=bar.

        :return: consumers map
        :raises: LTIException if environment variables are not found
        """
        consumers = {}
        for env in os.environ:
            if env.startswith('CONSUMER_KEY_SECRET_'):
                key = env[20:]  # Strip off the CONSUMER_KEY_SECRET_ prefix
                # TODO: remove below after live test
                # consumers[key] = {"secret": os.environ[env], "cert": 'NA'}
                consumers[key] = {"secret": os.environ[env], "cert": None}
        if not consumers:
            raise LTIException("No consumers found. Chalice stores "
                               "consumers in Lambda environment variables. "
                               "Have you created the environment variables?")
        return consumers

    def verify_request(self):
        """
        Verify LTI request

        :raises: LTIException if request validation failed
        """
        request = self.lti_kwargs['app'].current_request
        if request.method == 'POST':
            # Chalice expects JSON and does not nativly support forms data in
            # a post body. The below is copied from the parsing of query
            # strings as implimented in match_route of Chalice local.py
            parsed_url = request.raw_body.decode()
            parsed_qs = parse_qs(parsed_url, keep_blank_values=True)
            params = {k: v[0] for k, v in parsed_qs .items()}
        else:
            params = request.query_params
        log.debug(params)
        log.debug('verify_request?')
        try:
            # Chalice does not have a url property therefore building it.
            hostname = request.headers['host']
            path = request.context['path']
            # TODO: Chalice local is not setting the "path"
            url = urlunparse(("https", hostname, path, "", "", ""))
            verify_request_common(self._consumers(), url,
                                  request.method, request.headers,
                                  params)
            log.debug('verify_request success')

            # All good to go, store all of the LTI params into a
            # session dict for use in views
            for prop in LTI_PROPERTY_LIST:
                if params.get(prop, None):
                    log.debug("params %s=%s", prop, params.get(prop, None))
                    self.session[prop] = params[prop]

            # Set logged in session key
            self.session[LTI_SESSION_KEY] = True
            return True
        except LTIException:
            log.debug('verify_request failed')
            for prop in LTI_PROPERTY_LIST:
                if self.session.get(prop, None):
                    del self.session[prop]

            self.session[LTI_SESSION_KEY] = False
            raise

    @property
    def response_url(self):
        """
        Returns remapped lis_outcome_service_url
        uses PYLTI_URL_FIX map to support edX dev-stack

        :return: remapped lis_outcome_service_url
        """
        url = ""
        url = self.session['lis_outcome_service_url']
        # TODO: Remove this section if not needed
        # app_config = self.config
        # urls = app_config.get('PYLTI_URL_FIX', dict())
        # # url remapping is useful for using devstack
        # # devstack reports httpS://localhost:8000/ and listens on HTTP
        # for prefix, mapping in urls.items():
        #     if url.startswith(prefix):
        #         for _from, _to in mapping.items():
        #             url = url.replace(_from, _to)
        return url

    def _verify_any(self):
        """
        Verify that request is in session or initial request

        :raises: LTIException
        """
        raise LTIException("The Request Type any is not "
                           "supported because Chalice does not support "
                           "session state. Change the Request Type to "
                           "initial or omit it from the declaration.")

    @staticmethod
    def _verify_session():
        """
        Verify that session was already created

        :raises: LTIException
        """
        raise LTIException("The Request Type session is not "
                           "supported because Chalice does not support "
                           "session state. Change the Request Type to "
                           "initial or omit it from the declaration.")

    @staticmethod
    def close_session():
        """
        Invalidates session
        :raises: LTIException
        """
        raise LTIException("Can not close session. Chalice does "
                           "not support session state.")


def lti(app, request='initial', error=default_error, role='any',
        *lti_args, **lti_kwargs):
    """
    LTI decorator
    :param: app - Chalice App object.
    :param: error - Callback if LTI throws exception (optional).
    :param: request - Request type from
        :py:attr:`pylti.common.LTI_REQUEST_TYPE`. (default: any)
    :param: roles - LTI Role (default: any)
    :return: wrapper
    """
    def _lti(function):
        """
        Inner LTI decorator
        :param: function:
        :return:
        """

        @wraps(function)
        def wrapper(*args, **kwargs):
            """
            Pass LTI reference to function or return error.
            """
            try:
                the_lti = LTI(lti_args, lti_kwargs)
                the_lti.verify()
                the_lti._check_role()  # pylint: disable=protected-access
                kwargs['lti'] = the_lti
                return function(*args, **kwargs)
            except LTIException as lti_exception:
                error = lti_kwargs.get('error')
                exception = dict()
                exception['exception'] = lti_exception
                exception['kwargs'] = kwargs
                exception['args'] = args
                return error(exception=exception)

        return wrapper

    lti_kwargs['request'] = request
    lti_kwargs['error'] = error
    lti_kwargs['role'] = role

    if (not app) or isinstance(app, Chalice):
        lti_kwargs['app'] = app
        return _lti
    else:
        # We are wrapping without arguments
        lti_kwargs['app'] = None
        return _lti(app)
