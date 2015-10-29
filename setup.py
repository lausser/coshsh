from setuptools import setup

setup(name='coshsh',
      version='2.0',
      description='Coshsh - config generator for monitoring systems',
      url='http://github.com/lausser/coshsh',
      author='Gerhard Lausser',
      author_email='gerhard.lausser@consol.de',
      license='GPLv2',
      packages=['coshsh'],
      data_files=[('', ['recipes/default/templates/os_windows_fs.tpl'])],
      zip_safe=False)

