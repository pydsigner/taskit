#! /usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys

import taskit

long_description = '''TaskIt -- A light-weight task management library.

TaskIt is a light-weight library to turn a function into a full-featured, 
threadable task. It is completely X-Python Compatible and has no external 
dependencies. The simple version is completely self-contained, whereas the 
distributed version has a simple, obvious way to connect with the backends.'''


def main():
    setup(script_args=sys.argv[1:] if len(sys.argv) > 1 else ['install'],
          name='taskit',
          version=taskit.__version__,
          description='TaskIt -- A light-weight task management library.',
          long_description=long_description,
          author='Daniel Foerster/pydsigner',
          author_email='pydsigner@gmail.com',
          packages=['taskit'],
          package_data={'taskit': ['doc/*.md']},
          license='LGPLv3',
          url='http://github.com/pydsigner/taskit',
          classifiers=['Development Status :: 5 - Production/Stable',
                       'Intended Audience :: Developers',
                       'Operating System :: MacOS :: MacOS X',
                       'Operating System :: Microsoft :: Windows',
                       'Operating System :: POSIX',
                       'Programming Language :: Python',])

if __name__ == '__main__':
    main()
