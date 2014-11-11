# -*- coding: utf-8 -*-
#
# PyLTI documentation build configuration file, created by
# sphinx-quickstart on Mon Nov  3 11:17:08 2014.
#

import sys
import os

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.coverage',
]

templates_path = ['_templates']

source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u'PyLTI'
copyright = u'2014, ODL Engineering'

static_mod = os.path.join('..','..', 'pylti', '__init__.py')
execfile(static_mod)
version = VERSION
release = VERSION

exclude_patterns = []

pygments_style = 'sphinx'

html_theme = 'sphinxdoc'

html_static_path = ['_static']

htmlhelp_basename = 'PyLTIdoc'


latex_elements = {
}

latex_documents = [
  ('index', 'PyLTI.tex', u'PyLTI Documentation',
   u'Ivica Ceraj (ODL Engineering)', 'manual'),
]

man_pages = [
    ('index', 'pylti', u'PyLTI Documentation',
     [u'Ivica Ceraj (ODL Engineering)'], 1)
]

texinfo_documents = [
  ('index', 'PyLTI', u'PyLTI Documentation',
   u'Ivica Ceraj (ODL Engineering)', 'PyLTI', 'Python LTI decorators.',
   'Miscellaneous'),
]

