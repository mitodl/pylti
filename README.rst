PyLTI - LTI done right
=========================

.. image:: https://secure.travis-ci.org/mitodl/pylti.png?branch=develop
  :target: https://secure.travis-ci.org/mitodl/pylti
.. image:: https://pypip.in/d/pylti/badge.png
  :target: https://pypi.python.org/pypi/PyLTI/
.. image:: https://coveralls.io/repos/mitodl/pylti/badge.png?branch=develop
  :target: https://coveralls.io/r/mitodl/pylti?branch=develop

PyLTI is a Python implementation of the LTI specification [#f1]_.  It supports
LTI 1.1.1 and LTI 2.0.  While it was written with edX as its LTI consumer, it
is a complete implementation of the LTI specification and can be used with any
learning management system that supports LTI.

A feature of PyLTI is the way it is used in the creation of an LTI tool.  PyLTI
is written as a library that exposes an API.  This separation of concerns
enables a developer to focus on the business logic of their tool and support of
their framework of choice.

To demonstrate this usage, there are also a collection of example LTI tools
written to support different Python web frameworks.

=========  ============
Framework  Example code
=========  ============
Flask      mit_lti_flask_sample
Django     mit_lti_django_sample
Bottle     mit_lti_bottle_sample
=========  ============


.. rubric:: Footnotes

.. [#f1] The Learning Tools Interoperability (LTI) specification is an
   initiative of IMS.  Their site `http://developers.imsglobal.org/
   <http://developers.imsglobal.org/>`_ contains a description of LTI as well as
   the current LTI specification.
