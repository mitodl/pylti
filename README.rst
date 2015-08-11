PyLTI - LTI done right
=========================
:PyLTI: Python implementation of LTI
:Version: 0.4.0
:Author: MIT Office of Digital Learning
:Homepage: http://odl.mit.edu
:License: BSD

.. image:: https://secure.travis-ci.org/mitodl/pylti.png?branch=develop
  :target: https://secure.travis-ci.org/mitodl/pylti
.. image:: https://pypip.in/d/pylti/badge.png
  :target: https://pypi.python.org/pypi/PyLTI/
.. image:: https://coveralls.io/repos/mitodl/pylti/badge.png?branch=develop
  :target: https://coveralls.io/r/mitodl/pylti?branch=develop

.. _Documentation: http://pylti.readthedocs.org/en/latest/

PyLTI is a Python implementation of the LTI specification [#f1]_.  It supports
LTI 1.1.1 and LTI 2.0.  While it was written with edX [#f2]_ as its LTI consumer, it
is a complete implementation of the LTI specification and can be used with any
learning management system that supports LTI.

A feature of PyLTI is the way it is used in the creation of an LTI tool.  PyLTI
is written as a library that exposes an API.  This separation of concerns
enables a developer to focus on the business logic of their tool and support of
their framework of choice.

To demonstrate this usage, there are also a collection of example LTI tools
written to support different Python web frameworks.

=========  ============
Framework  Example
=========  ============
Flask      `mit_lti_flask_sample
           <https://github.com/mitodl/mit_lti_flask_sample>`_
           A skeleton example for the Flask framework that consumes the PyLTI library
=========  ============

Dependencies:
=============
* Python 2.7+
* oauth 1.0.1+
* oauth2 1.5.211+
* httplib2 0.9+

Development dependencies:
=========================
* Flask 0.10.1
* httpretty 0.8.3
* oauthlib 0.6.3
* pyflakes 0.8.1
* pytest 2.6.3
* pytest-cache 1.0
* pytest-cov 1.8.0
* pytest-flakes 0.2
* pytest-pep8 1.0.6
* sphinx 1.2.3

Documentation_ is available on readthedocs.

Licensing
=========
PyLTI is licensed under the BSD license, version January 9, 2008.  See
license.rst for the full text of the license.

.. rubric:: Footnotes

.. [#f1] The Learning Tools Interoperability (LTI) specification is an
   initiative of IMS.  Their site `http://developers.imsglobal.org/
   <http://developers.imsglobal.org/>`_ contains a description of LTI as well as
   the current LTI specification.
.. [#f2] EdX offers interactive online classes and MOOCs from the world’s best
   universities. Online courses from MITx, HarvardX, BerkeleyX, UTx and many
   other universities.  EdX is a non-profit online initiative created by
   founding partners Harvard and MIT. `code.edx.org <http://code.edx.org>`_
