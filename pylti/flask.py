# -*- coding: utf-8 -*-
"""
    PyLTI decorator implementation for flask framework
"""
from __future__ import absolute_import
from functools import wraps, partial
import logging

from flask import session, request

from .common import (LTI_SESSION_KEY, LTI_PROPERTY_LIST,
                     LTI_ROLES, verify_request_common, post_message,
                     LTIException, LTIRoleException, LTINotInSessionException,
                     generate_request_xml)


log = logging.getLogger('pylti.flask')  # pylint: disable=invalid-name


class LTIVerificationFailedException(Exception):
    """
    LTI Verification failed exception
    """
    pass


class LTI(object):
    def __init__(self, lti_args, lti_kwargs):
        self.lti_args = lti_args
        self.lti_kwargs = lti_kwargs
        self.nickname = self.name()

    def name(self):
        if 'lis_person_sourcedid' in session:
            return session['lis_person_sourcedid']
        elif 'lis_person_contact_email_primary' in session:
            return session['lis_person_contact_email_primary']
        elif 'user_id' in session:
            return session['user_id']
        else:
            return ''

    def verify(self):
        log.debug('verify request={}'.format(self.lti_kwargs.get('request')))
        if self.lti_kwargs.get('request') == 'session':
            self._verify_session()
        elif self.lti_kwargs.get('request') == 'initial':
            self.verify_request()
        elif self.lti_kwargs.get('request') == 'any':
            self._verify_any()
        else:
            raise LTIException("Unknown request type")

    def _verify_any(self):
        log.debug('verify_any enter')
        try:
            self._verify_session()
        except LTINotInSessionException:
            self.verify_request()

    def _verify_session(self):
        if not session.get(LTI_SESSION_KEY, False):
            log.debug('verify_session failed')
            raise LTINotInSessionException('Session expired or unavailable')

    def _consumers(self):
        app_config = self.lti_kwargs['app'].config
        config = app_config.get('PYLTI_CONFIG', dict())
        consumers = config.get('consumers', dict())
        return consumers

    def key(self):
        return session['oauth_consumer_key']

    def message_identifier_id(self):
        return "edX_fix"

    def lis_result_sourcedid(self):
        return session['lis_result_sourcedid']

    def role(self):
        return session['roles']

    def is_role(self, role):
        log.debug("is_role {}".format(role))
        roles = session['roles']
        if role in LTI_ROLES:
            list = LTI_ROLES[role]
            log.debug("is_role roles_list={} role={} in list={}"
                      .format(list, roles, roles in list))
            return roles in list
        else:
            raise LTIException("Unknown role {}.".format(role))

    def check_role(self):
        role = u'any'
        if 'role' in self.lti_kwargs:
            role = self.lti_kwargs['role']
        log.debug("check_role lti_role={} decorator_role={}"
                  .format(self.role(), role))
        if not self.is_role(role):
            raise LTIRoleException('Not authorized.')

    def response_url(self):
        url = session['lis_outcome_service_url']
        app_config = self.lti_kwargs['app'].config
        urls = app_config.get('PYLTI_URL_FIX', dict())
        # url remapping is useful for using devstack
        # devstack reports httpS://localhost:8000/ and listens on HTTP
        for prefix, mapping in urls.iteritems():
            if url.startswith(prefix):
                for _from, _to in mapping.iteritems():
                    url = url.replace(_from, _to)
        return url

    def verify_request(self):
        if request.method == 'POST':
            params = request.form.to_dict()
        else:
            params = request.args.to_dict()
        log.debug(params)

        log.debug('verify_request?')
        try:
            verify_request_common(self._consumers(), request.url,
                                  request.method, request.headers, params)
            log.debug('verify_request success')

            # All good to go, store all of the LTI params into a
            # session dict for use in views
            for prop in LTI_PROPERTY_LIST:
                if params.get(prop, None):
                    log.debug("params {}={}".format(prop,
                                                    params.get(prop, None)))
                    session[prop] = params[prop]

            # Set logged in session key
            session[LTI_SESSION_KEY] = True
            return True
        except LTIException:
            log.debug('verify_request failed')
            for prop in LTI_PROPERTY_LIST:
                if session.get(prop, None):
                    del session[prop]

            session[LTI_SESSION_KEY] = False
            raise

    def post_grade(self, grade):
        message_identifier_id = self.message_identifier_id()
        operation = 'replaceResult'
        lis_result_sourcedid = self.lis_result_sourcedid()
        # # edX devbox fix
        score = float(grade)
        if 0 <= score <= 1.0:
            xml = generate_request_xml(
                message_identifier_id, operation, lis_result_sourcedid,
                score)
            post_message(self._consumers(), self.key(),
                         self.response_url(), xml)
            return True

        return False

    def close_session(self):
        for prop in LTI_PROPERTY_LIST:
            if session.get(prop, None):
                del session[prop]
        session[LTI_SESSION_KEY] = False


def lti(*lti_args_out, **lti_kwargs_out):
    def _lti(function, lti_args=None, lti_kwargs=None):
        @wraps(function)
        def wrapper(*args, **kwargs):
            try:
                the_lti = LTI(lti_args, lti_kwargs)
                the_lti.verify()
                the_lti.check_role()
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

    ret = partial(_lti, *lti_args_out,
                  lti_args=lti_args_out, lti_kwargs=lti_kwargs_out)

    return ret
