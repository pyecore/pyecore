#!/usr/bin/env python

from setuptools import setup

packages = ['pyecore',
            'pyecore.resources',
            'pyecore.type']

setup(
    name='pyecore-py2',
    version='0.7.2-dev',
    description=('A Python(ic) Implementation of the Eclipse Modeling '
                 'Framework (EMF/Ecore), Python 2.7 backport'),
    long_description=open('README.rst').read(),
    keywords='model metamodel EMF Ecore MDE',
    url='https://github.com/pyecore/pyecore',
    author='Vincent Aranega',
    author_email='vincent.aranega@gmail.com',

    packages=packages,
    package_data={'': ['README.rst', 'LICENSE', 'CHANGELOG.rst']},
    include_package_data=True,
    install_requires=['enum34',
                      'chainmap',
                      'ordered-set',
                      'lxml'],
    tests_require={'pytest'},
    license='BSD 3-Clause',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: BSD License',
    ]
)
