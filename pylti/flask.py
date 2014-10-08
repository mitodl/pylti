from __future__ import absolute_import
from flask import Flask, session, request
from functools import wraps, partial
from .common import LTI_SESSION_KEY, LTI_PROPERTY_LIST, LTI_STAFF_ROLES, verify_request_common, LTIException,LTINotInSessionException

import logging
log = logging.getLogger('pylti.flask')


# request = 'any' || 'initial' || 'session'


class LTIVerificationFailedException(Exception):
    pass

class LTI():
    def __init__(self, lti_args, lti_kwargs):
        self.lti_args = lti_args
        self.lti_kwargs = lti_kwargs

        self.nickname = 'nickname'

    def verify(self):
        log.debug('verify request={}'.format( self.lti_kwargs.get('request')))
        if ( self.lti_kwargs.get('request') == 'session' ):
            self.verify_session()
        elif ( self.lti_kwargs.get('request') == 'initial'):
            self.verify_request()
        elif ( self.lti_kwargs.get('request') == 'any'):
            self.verify_any()
        else:
            raise LTIException()

    def verify_any(self):
        log.debug('verify_any enter')
        try:
            self.verify_session()
        except LTINotInSessionException as e:
            self.verify_request()

    def verify_session(self):
        if not session.get(LTI_SESSION_KEY, False):
            log.debug('verify_session failed')
            raise LTINotInSessionException()

    def _consumers(self):
        app_config = self.lti_kwargs['app'].config
        config = app_config.get('PYLTI_CONFIG',dict())
        consumers = config.get('consumers',dict())
        return consumers

    def verify_request(self):
        if request.method == 'POST':
            params = request.form.to_dict()
        else:
            params = request.args.to_dict()
        log.debug(params)

        log.debug('verify_request?')
        if verify_request_common(self._consumers(),request.url, request.method, request.headers, params):
            log.debug('verify_request success')

            # All good to go, store all of the LTI params into a
            # session dict for use in views
            for prop in LTI_PROPERTY_LIST:
                if params.get(prop, None):
                    session[prop] = params[prop]

            # Set logged in session key
            session[LTI_SESSION_KEY] = True
            return True
        else:
            log.debug('verify_request failed')
            for prop in LTI_PROPERTY_LIST:
                if session.get(prop, None):
                    del session[prop]

            session[LTI_SESSION_KEY] = False
            raise LTIException

    def post_grade(self, grade):
        print "Grade {}".format(grade)
        return False

    def close_session(self):
        for prop in LTI_PROPERTY_LIST:
            if session.get(prop, None):
                del session[prop]
        session[LTI_SESSION_KEY] = False



def lti(*lti_args, **lti_kwargs):
    def _lti(f, lti_args=[], lti_kwargs=dict()):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                the_lti = LTI(lti_args,lti_kwargs)
                the_lti.verify()
                kwargs['lti'] = the_lti
                ret = f(*args, **kwargs)
                return ret
            except LTIException as e:
                error = lti_kwargs.get('error')
                exception = dict()
                exception['exception']=e
                exception['kwargs']=kwargs
                exception['args']=args
                ret = error(exception=exception)
                return ret
        return wrapper

    if len(lti_args) == 1 and callable(lti_args[0]):
        # No arguments, this is the decorator
        # Set default values for the arguments
        ret = _lti(lti_args[0])
    else:
        ret = partial(_lti, *lti_args, lti_args=lti_args, lti_kwargs=lti_kwargs)

    return ret


