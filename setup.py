#! /usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import sys

#############################################################################
### Main setup stuff
#############################################################################

def main():
    
    # perform the setup action
    import taskit
    setup_args = {
        'script_args': sys.argv[1:] if len(sys.argv) > 1 else ['install'],
        'name': 'taskit',
        'version': taskit.__version__,
        'description': 'TaskIt -- A light-weight task management library.',
        'long_description': 'TaskIt -- A light-weight task management library.',
        'author': 'Daniel Foerster/pydsigner',
        'author_email': 'pydsigner@gmail.com',
        'packages': ['taskit'],
        'license': 'LGPLv3',
        'url': "http://github.com/pydsigner/taskit",
        'classifiers': [
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Operating System :: MacOS :: MacOS X',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: POSIX',
            'Programming Language :: Python',
        ]}
    setup(**setup_args)

if __name__ == '__main__':
    main()
