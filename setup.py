#!/usr/bin/env python

import sys
from setuptools import setup


version = tuple(sys.version_info[:2])

if version < (3, 3):
    sys.exit('Sorry, Python < 3.3 is not supported')

requires = ['ordered-set>=4.0.1',
            'restrictedpython>=4.0b6',
            'future-fstrings']

if version == (3, 4):
    requires.append('lxml<4.4.0')
else:
    requires.append('lxml')

packages = ['pyecore',
            'pyecore.resources',
            'pyecore.type']

setup(
    name='pyecore',
    version='0.12.1',
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
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
    ]
)
