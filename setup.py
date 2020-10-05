#!/usr/bin/env python

# -*- coding: utf-8 -*-

import sys
try:
    python_version = sys.version_info
except:
    python_version = (1, 5)
if python_version < (2, 4):
    sys.exit("coshsh requires python 2.4.x and newer")
elif python_version >= (3,):
    sys.exit("coshsh requires python 2.x")

from setuptools import setup
from distutils import log
from distutils.command.install import install as _install
from distutils.command.install_data import install_data as _install_data
from distutils.core import setup, Command

import glob
import os

class CoshshTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        if 'PYTHONPATH' in os.environ:
            os.environ['PYTHONPATH'] += ":" + os.getcwd()
        else:
            os.environ['PYTHONPATH'] = os.getcwd()
        os.chdir('tests')
        for test in glob.glob('test_*.py'):
            log.info('Running test ' + test)
            errno = subprocess.call([sys.executable, test])
            if errno != 0:
                raise SystemExit(errno)


class install(_install):
    def run(self):
        _install.run(self)


class install_data(_install_data):
    def run(self):
        _install_data.run(self)


setup(name='coshsh',
      version='5.6.2.1',
      description='Coshsh - config generator for monitoring systems',
      url='http://github.com/lausser/coshsh',
      author='Gerhard Lausser',
      author_email='gerhard.lausser@consol.de',
      license='AGPLv3',
      keywords=['nagios', 'icinga', 'naemon', 'shinken', 'prometheus', 'monitoring'],
      packages=['coshsh'],
      data_files=[
          (os.path.join('recipes', 'default', 'classes'), 
              glob.glob(os.path.join('recipes', 'default', 'classes', '*.py'))),
          (os.path.join('recipes', 'default', 'templates'), 
              glob.glob(os.path.join('recipes', 'default', 'templates', '*.tpl')))
      ],
      scripts=['bin/coshsh-cook', 'bin/coshsh-create-template-tree'],
      cmdclass={'install_data': install_data, 'install': install, 'test': CoshshTest},
      zip_safe=False)

