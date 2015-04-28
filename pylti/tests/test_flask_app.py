"""
Test pylti/test_flask_app.py module
"""
from flask import Flask, session

from pylti.flask import lti as lti_flask
from pylti.common import LTI_SESSION_KEY

app = Flask(__name__)  # pylint: disable=invalid-name


class ExceptionHandler(object):
    """
    Custom exception handler.
    """
    exception = None

    def set(self, exception):
        """
        Setter: set class variable exception.
        """
        self.exception = exception

    def get(self):
        """
        Return exception if not None otherwise returns None.
        """
        if self.exception is None:
            return None
        else:
            return self.exception['exception']

    def reset(self):
        """
        Reset variable exception
        """
        self.exception = None

app_exception = ExceptionHandler()  # pylint: disable=invalid-name


def error(exception):
    """
    Set exception to exception handler and returns error string.
    """
    app_exception.set(exception)
    return "error"


@app.route("/unknown_protection")
@lti_flask(error=error, app=app, request='notreal')
def unknown_protection(lti):
    # pylint: disable=unused-argument,
    """
    access route with unknown protection

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"  # pragma: no cover


@app.route("/no_app")
@lti_flask(error=error)
def no_app(lti):
    # pylint: disable=unused-argument,
    """
    use decorator without specifying LTI, raise exception

    :param lti: `lti` object
    """
    # Check that we have the app in our lti object and raise if we
    # don't
    if not lti.lti_kwargs['app']:  # pragma: no cover
        raise Exception(
            'The app is null and is not properly getting current_app'
        )
    return 'hi'


@app.route("/any")
@lti_flask(error=error, request='any', app=app)
def any_route(lti):
    # pylint: disable=unused-argument,
    """
    access route with 'any' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/session")
@lti_flask(error=error, request='session', app=app)
def session_route(lti):
    # pylint: disable=unused-argument,
    """
    access route with 'session' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial", methods=['GET', 'POST'])
@lti_flask(error=error, request='initial', app=app)
def initial_route(lti):
    # pylint: disable=unused-argument,
    """
    access route with 'initial' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/name", methods=['GET', 'POST'])
@lti_flask(error=error, request='initial', app=app)
def name(lti):
    """
    access route with 'initial' request

    :param lti: `lti` object
    :return: string "hi"
    """
    return lti.name


@app.route("/initial_staff", methods=['GET', 'POST'])
@lti_flask(error=error, request='initial', role='staff', app=app)
def initial_staff_route(lti):
    # pylint: disable=unused-argument,
    """
    access route with 'initial' request and 'staff' role

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial_unknown", methods=['GET', 'POST'])
@lti_flask(error=error, request='initial', role='unknown', app=app)
def initial_unknown_route(lti):
    # pylint: disable=unused-argument,
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
@lti_flask(error=error, request='session', app=app)
def logout_route(lti):
    """
    access 'close_session' route

    :param lti: `lti` object
    :return: string "session closed"
    """
    lti.close_session()
    return "session closed"


@app.route("/post_grade/<float:grade>")
@lti_flask(error=error, request='session', app=app)
def post_grade(grade, lti):
    """
    access route with 'session' request

    :param lti: `lti` object
    :return: string "grade={}"
    """
    ret = lti.post_grade(grade)
    return "grade={}".format(ret)


@app.route("/post_grade2/<float:grade>")
@lti_flask(error=error, request='session', app=app)
def post_grade2(grade, lti):
    """
    access route with 'session' request

    :param lti: `lti` object
    :return: string "grade={}"
    """
    ret = lti.post_grade2(grade)
    return "grade={}".format(ret)


@app.route("/default_lti")
@lti_flask
def default_lti(lti=lti_flask):
    # pylint: disable=unused-argument,
    """
    Make sure default LTI decorator works.
    """
    return 'hi'  # pragma: no cover
