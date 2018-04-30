import re
import ast
import sys
from setuptools import setup, find_packages


has_enum = sys.version_info >= (3, 4)


_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('dmapiclient/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='digitalmarketplace-apiclient',
    version=version,
    url='https://github.com/alphagov/digitalmarketplace-apiclient',
    license='MIT',
    author='GDS Developers',
    description='Digital Marketplace Data and Search API clients',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==0.10.1',
        'backoff==1.0.7',
        'monotonic==0.3',
        'requests==2.18.4',
        'six==1.11.0'
    ] + ([] if has_enum else ['enum34==1.1.6'])
)
