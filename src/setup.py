from setuptools import setup, find_packages

setup(name='simplisafe-python',
      version='1.0.3',
      description='Python 3 support for SimpliSafe alarm',
      url='https://github.com/w1ll1am23/simplisafe-python',
      author='William Scanlon',
      license='MIT',
      install_requires=['requests>=2.0'],
      tests_require=['mock'],
      test_suite='tests',
      packages=find_packages(exclude=["dist", "*.test", "*.test.*", "test.*", "test"]),
      zip_safe=True)
