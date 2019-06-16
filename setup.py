#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
import ast

""" Installer for yolk1977 """

def version():
    """ Return version string """
    with open('yolk/__init__.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s

with open('README.rst') as readme:
    setup(
        name='yolk1977',
        license='BSD License',
        version=version(),
        description='Command-line tool for querying PyPI and Python packages '
                    'installed on your system.',
        long_description=readme.read(),
        maintainer='Alexander Bohn',
        author='Rob Cakebread',
        url='https://github.com/fish2000/yolk',
        keywords='PyPI,setuptools,cheeseshop,distutils,eggs,package,'
                 'management',
        classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Topic :: Software Development :: Libraries :: Python Modules',
        ],
        packages=['yolk'],
        package_dir={ 'yolk' : 'yolk' },
        entry_points={'console_scripts': ['yolk1977 = yolk.cli:main',
                                          'yolk = yolk.cli:main']}
    )
