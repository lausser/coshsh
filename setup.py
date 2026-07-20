import sys
import os

# Python < 3.8 compat: coshsh sources use "from __future__ import annotations"
# (PEP 563) which is a compile-time SyntaxError on Python 3.6. The
# coshsh_pycompat import hook strips these at import time, so byte-compilation
# during install would fail.  Skip it — .pyc files are created lazily on first
# import, where the hook is already active.
if sys.version_info < (3, 8):
    sys.dont_write_bytecode = True

from setuptools import setup
import glob

setup(name='coshsh',
      version='13.1',
      python_requires='>=3.8',
      description='Coshsh - config generator for monitoring systems',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      url='http://github.com/lausser/coshsh',
      author='Gerhard Lausser',
      author_email='gerhard.lausser@consol.de',
      license='AGPLv3',
      keywords=['nagios', 'icinga', 'naemon', 'shinken', 'prometheus', 'monitoring'],
      packages=['coshsh'],
      py_modules=['coshsh_pycompat'],
      data_files=[
          (os.path.join('recipes', 'default', 'classes'),
              glob.glob(os.path.join('recipes', 'default', 'classes', '*.py'))),
          (os.path.join('recipes', 'default', 'templates'),
              glob.glob(os.path.join('recipes', 'default', 'templates', '*.tpl')))
      ],
      scripts=['bin/coshsh-cook', 'bin/coshsh-create-template-tree'],
      zip_safe=False)
