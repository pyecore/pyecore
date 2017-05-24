#!/usr/bin/env python

import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 3):
    sys.exit('Sorry, Python < 3.3 is not supported')

requires = ['ordered-set', 'lxml']
if sys.version_info < (3, 4):
    requires.append('enum34')


setup(
    name='pyecore',
    version='0.5.0',
    description=('A Python(ic) Implementation of the Eclipse Modeling '
                 'Framework (EMF/Ecore)'),
    long_description=open('README.rst').read(),
    keywords='model metamodel EMF Ecore MDE',
    url='https://github.com/pyecore/pyecore',
    author='Vincent Aranega',
    author_email='vincent.aranega@gmail.com',

    packages=find_packages(exclude=['examples', 'tests']),
    package_data={'': ['LICENSE',
                       'README.rst']},
    include_package_data=True,
    install_requires=requires,
    tests_require={'pytest'},

    license='BSD 3-Clause',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
    ]
)
