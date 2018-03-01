from chalice import Chalice
from pylti.chalice import lti as lti_chalice
from pylti.tests.test_common import ExceptionHandler

app = Chalice(__name__)
app_exception = ExceptionHandler()  # pylint: disable=invalid-name


def error(exception):
    """
    Set exception to exception handler and returns error string.
    """
    app_exception.set(exception)
    return "error"


@app.route("/unknown_protection")
@lti_chalice(error=error, app=app, request='notreal')
def unknown_protection(lti):
    # pylint: disable=unused-argument,
    """
    Access route with unknown protection.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"  # pragma: no cover


@app.route("/any")
@lti_chalice(error=error, request='any', app=app)
def any_route(lti):
    # pylint: disable=unused-argument,
    """
    Access route with 'any' request.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/session")
@lti_chalice(error=error, request='session', app=app)
def session_route(lti):
    # pylint: disable=unused-argument,
    """
    Access route with 'session' request.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial", methods=['GET'])
@lti_chalice(error=error, request='initial', app=app)
def initial_route(lti):
    # pylint: disable=unused-argument,
    """
    Access route with 'initial' request.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial", methods=['POST'],
           content_types=['application/x-www-form-urlencoded'])
@lti_chalice(error=error, request='initial', app=app)
def post_form(lti):
    # pylint: disable=unused-argument,
    """
    Access route with 'initial' request.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/name", methods=['GET', 'POST'])
@lti_chalice(error=error, request='initial', app=app)
def name(lti):
    """
    Access route with 'initial' request.

    :param lti: `lti` object
    :return: string "hi"
    """
    return lti.name


@app.route("/initial_staff", methods=['GET'])
@lti_chalice(error=error, request='initial', role='staff', app=app)
def initial_staff_route(lti):
    # pylint: disable=unused-argument,
    """
    Access route with 'initial' request and 'staff' role.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial_student", methods=['GET', 'POST'])
@lti_chalice(error=error, request='initial', role='student', app=app)
def initial_student_route(lti):
    # pylint: disable=unused-argument,
    """
    Access route with 'initial' request and 'student' role.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"


@app.route("/initial_unknown", methods=['GET', 'POST'])
@lti_chalice(error=error, request='initial', role='unknown', app=app)
def initial_unknown_route(lti):
    # pylint: disable=unused-argument,
    """
    Access route with 'initial' request and 'unknown' role.

    :param lti: `lti` object
    :return: string "hi"
    """
    return "hi"  # pragma: no cover


# @app.route("/close_session")
# @lti_chalice(error=error, request='session', app=app)
# def logout_route(lti):
#     """
#     Access 'close_session' route.

#     :param lti: `lti` object
#     :return: string "session closed"
#     """
#     lti.close_session()
#     return "session closed"


@app.route("/post_grade/{grade}")
@lti_chalice(error=error, request='initial', app=app)
def post_grade(grade, lti):
    """
    Access route with 'session' request.

    :param lti: `lti` object
    :return: string "grade={}"
    """
    ret = lti.post_grade(grade)
    return "grade={}".format(ret)


@app.route("/post_grade2/{grade}")
@lti_chalice(error=error, request='initial', app=app)
def post_grade2(grade, lti):
    """
    Access route with 'session' request.

    :param lti: `lti` object
    :return: string "grade={}"
    """
    ret = lti.post_grade2(grade)
    return "grade={}".format(ret)


@app.route("/default_lti")
@lti_chalice
def default_lti(lti=lti_chalice):
    # pylint: disable=unused-argument,
    """
    Make sure default LTI decorator works.
    """
    return 'hi'  # pragma: no cover
