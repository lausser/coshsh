from setuptools import setup
import glob
import os


setup(name='coshsh',
      version='2.0',
      description='Coshsh - config generator for monitoring systems',
      url='http://github.com/lausser/coshsh',
      author='Gerhard Lausser',
      author_email='gerhard.lausser@consol.de',
      license='GPLv2',
      packages=['coshsh'],
      data_files=[
          (os.path.join('recipes', 'default', 'classes'), 
              glob.glob(os.path.join('recipes', 'default', 'classes', '*.py'))),
          (os.path.join('recipes', 'default', 'templates'), 
              glob.glob(os.path.join('recipes', 'default', 'templates', '*.tpl')))
      ],
      scripts=['bin/coshsh-cook', 'bin/coshsh-create-template-tree'],
      zip_safe=False)

# http://stackoverflow.com/questions/10456279/python-setuptools-how-to-include-a-config-file-for-distribution-into-prefix
