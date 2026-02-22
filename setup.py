from setuptools import setup
import glob
import os

setup(name='coshsh',
      version='12.1',
      python_requires='>=3.12',
      description='Coshsh - config generator for monitoring systems',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
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
      zip_safe=False)
