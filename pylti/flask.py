from __future__ import absolute_import
from flask import Flask, session, request
from functools import wraps, partial
from .common import LTI_SESSION_KEY, LTI_PROPERTY_LIST, LTI_STAFF_ROLES, verify_request_common, post_message,LTIException,LTINotInSessionException
from lxml import etree

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

    def key(self):
        return session['oauth_consumer_key']

    def message_identifier_id(self):
        return "edX_fix"

    def lis_result_sourcedid(self):
        return session['lis_result_sourcedid']


    def response_url(self):
        url = session['lis_outcome_service_url']
        app_config = self.lti_kwargs['app'].config
        urls = app_config.get('PYLTI_URL_FIX',dict())
        ## url remapping is useful for using devstack
        ## devstack reports httpS://localhost:8000/ and listens on HTTP
        for prefix, map in urls.iteritems():
           if url.startswith( prefix):
               for _from, _to in map.iteritems():
                   url = url.replace(_from,_to)
        return url

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
                    log.debug( "params {}={}".format( prop,params.get(prop, None) ))
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

    def generate_request_xml(self,message_identifier_id,operation,lis_result_sourcedid,score):
        root = etree.Element('imsx_POXEnvelopeRequest', xmlns =
                    'http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0')

        header = etree.SubElement(root, 'imsx_POXHeader')
        header_info = etree.SubElement(header, 'imsx_POXRequestHeaderInfo')
        version = etree.SubElement(header_info, 'imsx_version')
        version.text = 'V1.0'
        message_identifier = etree.SubElement(header_info,
                'imsx_messageIdentifier')
        message_identifier.text = message_identifier_id
        body = etree.SubElement(root, 'imsx_POXBody')
        request = etree.SubElement(body, '%s%s' %(operation,
            'Request'))
        record = etree.SubElement(request, 'resultRecord')

        guid = etree.SubElement(record, 'sourcedGUID')

        sourcedid = etree.SubElement(guid, 'sourcedId')
        sourcedid.text = lis_result_sourcedid
        if not (score is None):
            result = etree.SubElement(record, 'result')
            result_score = etree.SubElement(result, 'resultScore')
            language = etree.SubElement(result_score, 'language')
            language.text = 'en'
            text_string = etree.SubElement(result_score, 'textString')
            text_string.text = score.__str__()
        log.debug( "XML Response: \n{}".format(etree.tostring(root, xml_declaration = True, encoding = 'utf-8')))
        return etree.tostring(root, xml_declaration = True, encoding = 'utf-8')

    def post_grade(self, grade):
        message_identifier_id = 'message_identifier_id'
        operation = 'replaceResult'
        lis_result_sourcedid = self.lis_result_sourcedid()
        ## edX devbox fix
        score = float(grade)
        if score <= 1.0 and score >= 0:
            xml = self.generate_request_xml(message_identifier_id,operation,lis_result_sourcedid,score)
            post_message(self._consumers(),self.key(),self.response_url(),xml)
            return True

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


