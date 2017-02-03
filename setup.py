import re
import ast
from setuptools import setup, find_packages


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
        'Flask>=0.10',
        'backoff==1.0.7',
        'enum34==1.1.2',
        'monotonic==0.3',
        'requests==2.7.0',
        'six==1.9.0'
    ]
)
