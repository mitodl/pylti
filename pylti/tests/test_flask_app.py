from flask import Flask, session

from pylti.flask import lti
from pylti.common import LTI_SESSION_KEY


app = Flask(__name__)


class ExceptionHandler(object):
    exception = None

    def set(self, exception):
        self.exception = exception

    def get(self):
        if self.exception is None:
            return None
        else:
            return self.exception['exception']

    def reset(self):
        self.exception = None

app_exception = ExceptionHandler()


def error(exception):
    app_exception.set(exception)
    return "error"


@app.route("/unknown_protection")
@lti(error=error, app=app)
def unknown_protection(lti):
    """
    access route with unknown protection

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"  # pragma: no cover


@app.route("/any")
@lti(error=error, request='any', app=app)
def any_route(lti):
    """
    access route with 'any' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/session")
@lti(error=error, request='session', app=app)
def session_route(lti):
    """
    access route with 'session' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial", methods=['GET', 'POST'])
@lti(error=error, request='initial', app=app)
def initial_route(lti):
    """
    access route with 'initial' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/name", methods=['GET', 'POST'])
@lti(error=error, request='initial', app=app)
def name(lti):
    """
    access route with 'initial' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return lti.name


@app.route("/initial_staff", methods=['GET', 'POST'])
@lti(error=error, request='initial', role='staff', app=app)
def initial_staff_route(lti):
    """
    access route with 'initial' request and 'staff' role

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial_unknown", methods=['GET', 'POST'])
@lti(error=error, request='initial', role='unknown', app=app)
def initial_unknown_route(lti):
    """
    access route with 'initial' request and 'unknown' role

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"  # pragma: no cover


@app.route("/setup_session")
def setup_session():
    """
    access 'setup_session' route with 'Student' role and oauth_consumer_key

    :return: string "session set"
    """
    session[LTI_SESSION_KEY] = True
    session['oauth_consumer_key'] = '__consumer_key__'
    session['roles'] = 'Student'
    return "session set"


@app.route("/close_session")
@lti(error=error, request='session', app=app)
def logout_route(lti):
    """
    access 'close_session' route

    :param lti: `lti` object
    :return: string "session closed"
    """
    lti.close_session()
    return "session closed"


@app.route("/post_grade/<float:grade>")
@lti(error=error, request='session', app=app)
def post_grade(grade, lti):
    """
    access route with 'session' request

    :param lti: `lti` object
    :return: string "grade={}"
    """
    ret = lti.post_grade(grade)
    return "grade={}".format(ret)


@app.route("/post_grade2/<float:grade>")
@lti(error=error, request='session', app=app)
def post_grade2(grade, lti):
    """
    access route with 'session' request

    :param lti: `lti` object
    :return: string "grade={}"
    """
    ret = lti.post_grade2(grade)
    return "grade={}".format(ret)
