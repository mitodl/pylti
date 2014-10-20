from flask import Flask, session, request
from pylti.flask import lti
from pylti.common import LTI_SESSION_KEY

app = Flask(__name__)

state = dict()

def error(exception):
    state['exception'] = exception
    return "error"


@app.route("/unknown_protection")
@lti(error=error, app=app)
def unknown_protection(self):
    return "hi" #pragma: no cover


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


@app.route("/setup_session")
def setup_session():
    session[LTI_SESSION_KEY] = True
    session['oauth_consumer_key'] = '__consumer_key__'
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

