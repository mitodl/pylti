Getting started with PyLTI using Flask
======================================

PyLTI provides authorization wrapper for Flask requests.

First make sure to import pylti implementation for your framework. In this case Flask.

.. code-block:: python

    from pylti.flask import lti

    app = Flask(__name__)

Next let's look at how we can protect landing page using pylti wrapper. Note two things:
 * We use *@lti* decorator to protect route
 * Route takes named argument *lti* which provides way to interact with LTI consumer

.. code-block:: python

    @app.route("/any")
    @lti(error=error, request='any', app=app)
    def any_route(lti):
        """
        In this example route /any is protected and initial or subsequent call
        to the URL will succeed. As you can see lti passed one keyword parameter
        lti object that can be used to inspect LTI session.

        :param: lti: `lti` object
        :return: string "html to return"
        """
        return "Landing page"


We may have different need, and maybe landing page should be only available for initial request.
To allow only initial requests to be accessible one can use *request='initial'* as an argument to the wrapper.

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

Or we may have different need, and maybe session page should be only available for subsequent request.
To allow only initial requests to be accessible one can use *request='session'* as an argument to the wrapper.

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


Some pages in your application may be applicable only to administrators.
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

Argument app is flask application, and argument error is function that gets called if access is denied.

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

