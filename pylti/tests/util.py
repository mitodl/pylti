# -*- coding: utf-8 -*-
"""
Test pylti/test_common.py module
"""


import os


TEST_DATA_ROOT = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data'
)

TEST_CLIENT_CERT = os.path.join(TEST_DATA_ROOT, 'certs', 'snakeoil.pem')
