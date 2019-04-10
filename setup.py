#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
import re
import os
import sys

description = """
This library provides an easy way to work with ADH-Tech GT521F52 fingerprint scanner.

Source code hosted on Github: https://github.com/CESARBR/GT521F52
"""

package = 'GT_521F52'
requirements = [
    'pyserial>=3.4.0'
]

setup(
    name='GT_521F52',
    version="1.0.0",
    description='Python ADH-Tech GT521F52 library',
    long_description=description,
    author='Lucas Costa Cabral',
    author_email='lcc2@cesar.org.br',
    url='https://github.com/CESARBR/GT521F52',
    packages=[
        'GT_521F52',
    ],
    include_package_data=True,
    install_requires=requirements,
    license="Apache-2.0",
    zip_safe=False,
    keywords='GT521F52,fingerprint,python',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
