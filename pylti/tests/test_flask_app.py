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
    return "hi"  # pragma: no cover


@app.route("/any")
@lti(error=error, request='any', app=app)
def any_route(lti):
    return "hi"


@app.route("/session")
@lti(error=error, request='session', app=app)
def session_route(lti):
    return "hi"


@app.route("/initial", methods=['GET', 'POST'])
@lti(error=error, request='initial', app=app)
def initial_route(lti):
    return "hi"


@app.route("/initial_staff", methods=['GET', 'POST'])
@lti(error=error, request='initial', role='staff', app=app)
def initial_staff_route(lti):
    return "hi"


@app.route("/initial_unknown", methods=['GET', 'POST'])
@lti(error=error, request='initial', role='unknown', app=app)
def initial_unknown_route(lti):
    return "hi"  # pragma: no cover


@app.route("/setup_session")
def setup_session():
    session[LTI_SESSION_KEY] = True
    session['oauth_consumer_key'] = '__consumer_key__'
    session['roles'] = 'Student'
    return "session set"


@app.route("/close_session")
@lti(error=error, request='session', app=app)
def logout_route(lti):
    lti.close_session()
    return "session closed"


@app.route("/post_grade/<float:grade>")
@lti(error=error, request='session', app=app)
def post_grade(grade, lti):
    ret = lti.post_grade(grade)
    return "grade={}".format(ret)
