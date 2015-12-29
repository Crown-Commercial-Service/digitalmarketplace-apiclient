import re
import ast
import pip.download
from pip.req import parse_requirements
from setuptools import setup, find_packages


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('dmutils/apiclient/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

requirements = list(parse_requirements('requirements.txt', session=pip.download.PipSession()))

install_requires = [str(r.req) for r in requirements]

setup(
    name='digitalmarketplace-apiclient',
    version=version,
    url='https://github.com/alphagov/digitalmarketplace-apiclient',
    license='MIT',
    author='GDS Developers',
    description='Digital Marketplace Data and Search API clients',
    long_description=__doc__,
    packages=find_packages(),
    namespace_packages=['dmutils'],
    include_package_data=True,
    install_requires=install_requires
)
