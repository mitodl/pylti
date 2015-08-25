.. PyLTI documentation master file, created by
   sphinx-quickstart on Mon Nov  3 11:17:08 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PyLTI's documentation!
=================================

Contents:

.. toctree::
   flask.rst
   pylti_common.rst
   pylti_flask.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Getting Started
==================


Changes
=======

v0.4.1
~~~~~~

- Pin mock to allow ``python setup.py test`` without setuptools upgrade

v0.4.0
~~~~~~

- Support for role lists (Sakai 10+) thanks to `@rickyrem <https://github.com/rickyrem>`_
- Added several files to distribution (including test data) thanks
  to @jtriley and `@layus <https://github.com/layus>`_
- Flask app is no longer required to be passed around as it uses
  ``current_app``
- Decorators no longer require parameters, i.e. ``@lti`` can be used,
  which defaults to allowing any role access
- Coursera support was added via the ``Learner`` role thanks to
  `@caioteixeira <https://github.com/caioteixeira>`_
- Choosing to allow ``any`` role, actually works with any role now.
  It used to require the role to be in a set of known roles thanks
  to `@velochy <https://github.com/velochy>`_
- Proper URL checking for https was fixed thanks to `@velochy <https://github.com/velochy>`_
