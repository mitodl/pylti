Getting started with PyLTI using Flask
======================================

PyLTI provides an authorization decorator for Flask requests.

To use ``pylti`` you will need to import the ``pylti`` Flask decorator, and create a Flask application.

.. code-block:: python

    from pylti.flask import lti

    app = Flask(__name__)

Next let's look at how we can protect the landing page using the ``pylti`` decorator. Note two things:
 * The *@lti* decorator protects the route
 * The route takes a named argument *lti* which interacts with an LTI consumer
   *lti* object is an instance of :py:class:`pylti.flask.LTI` .

.. code-block:: python

    @app.route("/any")
    @lti(error=error, request='any', app=app)
    def any_route(lti):
        """
        In this example route /any is protected and initial or subsequent calls
        to the URL will succeed. As you can see lti passed one keyword parameter
        lti object that can be used to inspect LTI session.

        :param: lti: `lti` object
        :return: string "html to return"
        """
        return "Landing page"


You may have different needs; maybe you want your landing page available only for the initial request.
For access on the initial requests only, use *request='initial'* as an argument to the decorator.

.. code-block:: python

    @app.route("/initial")
    @lti(error=error, request='initial', app=app)
    def initial_route(lti):
        """
        access route with 'initial' request only, subsequent requests are not allowed.

        :param: lti: `lti` object
        :return: string "Initial request"
        """
        return "Initial request"

You may want some pages available only after the initial page is visited.
To allow only subsequent requests to be accessible use *request='session'* as an argument to the decorator.

.. code-block:: python

    @app.route("/session")
    @lti(error=error, request='session', app=app)
    def session_route(lti):
        """
        access route with 'session' request

        :param: lti: `lti` object
        :return: string "Session request"
        """
        return "Session request"


Often times in your LTI Tool Provider, some pages are accessible only by administrators.
To protect those pages you can use *role* attribute.

.. code-block:: python

    @app.route("/initial_staff", methods=['GET', 'POST'])
    @lti(error=error, request='initial', role='staff', app=app)
    def initial_staff_route(lti):
        """
        access route with 'initial' request and 'staff' role

        :param: lti: `lti` object
        :return: string "hi"
        """
        return "Staff page"

*@lti* has a number of arguments. The required arguments
are *app*, *error* and *request*.  The *role* argument is optional.
Argument *app* is the Flask application.  Argument *error* is the function that gets called
if access is denied, or decorator fails for any other reason. *request* has already been
explained, and determines which type of LTI requests are allowed.
The *role* argument is optional.  Mapping between pylti roles and the roles defined in the LTI
standard is described by *pylti.common.LTI_ROLES*.

.. code-block:: python

    def error(exception):
        """
        Error receives one argument - exception
        exception is a dictionary with the following keys:
            exception['exception'] = lti_exception
            exception['kwargs'] = kwargs - keyword arguments passed to the route
            exception['args'] = args - positional arguments passed to teh route

        :param: exception: `exception` object
        :return: string "HTML in case of exception"
        """
        app_exception.set(exception)
        return "HTML to return"


