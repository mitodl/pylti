#!/usr/bin/env python
# Copyright 2009-2014 MIT ODL Engineering
#
# This file is part of PyLTI.
#
import os
import sys

if sys.version_info < (2, 6):
    error = "ERROR: PyLTI requires Python 2.6+ ... exiting."
    print >> sys.stderr, error
    sys.exit(1)

try:
    from setuptools import setup, find_packages
    from setuptools.command.test import test as TestCommand

    class PyTest(TestCommand):
        user_options = TestCommand.user_options[:]
        user_options += [
            ('coverage', 'C', 'Produce a coverage report for PyLTI'),
        ]

        def initialize_options(self):
            TestCommand.initialize_options(self)
            self.coverage = None

        def finalize_options(self):
            TestCommand.finalize_options(self)
            self.test_suite = True
            self.test_args = []
            if self.coverage:
                self.test_args.append('--cov')
                self.test_args.append('pylti')

        def run_tests(self):
            # import here, cause outside the eggs aren't loaded
            import pytest
            # Needed in order for pytest_cache to load properly
            # Alternate fix: import pytest_cache and pass to pytest.main
            import _pytest.config
            pm = _pytest.config.get_plugin_manager()
            pm.consider_setuptools_entrypoints()
            errno = pytest.main(self.test_args)
            sys.exit(errno)

    extra = dict(test_suite="pylti.tests",
                 tests_require= ["pytest-cov", "pytest-pep8", "pytest-flakes",
                                 "pytest","httpretty","flask"],
                 cmdclass={"test": PyTest},
                 install_requires=['oauth2','oauth','lxml','oauthlib'],
                 include_package_data=True,
                 #entry_points=dict(console_scripts=console_scripts),
                 zip_safe=False)
except ImportError:
    import string
    from distutils.core import setup

    def convert_path(pathname):
        """
        Local copy of setuptools.convert_path used by find_packages (only used
        with distutils which is missing the find_packages feature)
        """
        if os.sep == '/':
            return pathname
        if not pathname:
            return pathname
        if pathname[0] == '/':
            raise ValueError("path '%s' cannot be absolute" % pathname)
        if pathname[-1] == '/':
            raise ValueError("path '%s' cannot end with '/'" % pathname)
        paths = string.split(pathname, '/')
        while '.' in paths:
            paths.remove('.')
        if not paths:
            return os.curdir
        return os.path.join(*paths)

    def find_packages(where='.', exclude=()):
        """
        Local copy of setuptools.find_packages (only used with distutils which
        is missing the find_packages feature)
        """
        out = []
        stack = [(convert_path(where), '')]
        while stack:
            where, prefix = stack.pop(0)
            for name in os.listdir(where):
                fn = os.path.join(where, name)
                isdir = os.path.isdir(fn)
                has_init = os.path.isfile(os.path.join(fn, '__init__.py'))
                if '.' not in name and isdir and has_init:
                    out.append(prefix + name)
                    stack.append((fn, prefix + name + '.'))
        for pat in list(exclude) + ['ez_setup', 'distribute_setup']:
            from fnmatch import fnmatchcase
            out = [item for item in out if not fnmatchcase(item, pat)]
        return out

VERSION = __import__('pylti').VERSION

README = open('README.rst').read()

setup(
    name='PyLTI',
    version=VERSION,
    packages=find_packages(),
    package_data={'pylti.templates':
                  ['web/*.*', 'web/css/*', 'web/js/*']},
    license='Unknown',
    author='MIT ODL Engineering',
    author_email='odl-engineering@mit.edu',
    url="http://github.com/mitodl/pylti",
    description="PyLTI provides Python Implementation of IMS"
    " LTI interface that works with edX",
    long_description=README,
    classifiers=[
        'Environment :: Console',
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Other Audience',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Topic :: Education',
        'Topic :: Scientific/Engineering',
        'Topic :: System :: Distributed Computing',
        'Topic :: System :: Clustering',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    **extra
)

