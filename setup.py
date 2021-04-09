"""
API clients for Digital Marketplace Data API and Search API.
"""

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
    package_data={'dmapiclient': ['py.typed']},
    include_package_data=True,
    install_requires=[
        'requests<3,>=2.18.4',
    ],
    python_requires="~=3.6",
)
