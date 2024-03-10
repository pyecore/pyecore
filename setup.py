#!/usr/bin/env python

import sys
from setuptools import setup


version = tuple(sys.version_info[:2])

if version < (3, 3):
    sys.exit('Sorry, Python < 3.3 is not supported')

requires = ['ordered-set>=4.0.1',
            'restrictedpython>=5.3,>=6.1',
            'future-fstrings',
            'lxml']

packages = ['pyecore',
            'pyecore.resources',
            'pyecore.type']

setup(
    name='pyecore',
    version='0.14.1-dev',
    description=('A Python(ic) Implementation of the Eclipse Modeling '
                 'Framework (EMF/Ecore)'),
    long_description=open('README.rst').read(),
    keywords='model metamodel EMF Ecore MDE',
    url='https://github.com/pyecore/pyecore',
    author='Vincent Aranega',
    author_email='vincent.aranega@gmail.com',

    packages=packages,
    package_data={'': ['README.rst', 'LICENSE', 'CHANGELOG.rst']},
    include_package_data=True,
    install_requires=requires,
    tests_require=['pytest'],
    license='BSD 3-Clause',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
    ]
)
