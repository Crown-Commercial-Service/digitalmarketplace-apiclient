Digital Marketplace API client
=========================

[![Coverage Status](https://coveralls.io/repos/alphagov/digitalmarketplace-apiclient/badge.svg?branch=master&service=github)](https://coveralls.io/github/alphagov/digitalmarketplace-apiclient?branch=master)
[![Requirements Status](https://requires.io/github/alphagov/digitalmarketplace-apiclient/requirements.svg?branch=master)](https://requires.io/github/alphagov/digitalmarketplace-apiclient/requirements/?branch=master)

## What's in here?

API clients for Digital Marketplace [Data API](https://github.com/alphagov/digitalmarketplace-api) and
[Search API](https://github.com/alphagov/digitalmarketplace-search-api).

Originally was part of [Digital Marketplace Utils](https://github.com/alphagov/digitalmarketplace-utils).


## Running the tests

Install Python dependencies with pip

```
pip install -r requirements_for_test.txt
```

Run the tests

```
./scripts/run_tests.sh
```

## Usage examples

```python

data_client = apiclient.DataAPIClient(api_url, api_access_token)
services = data_client.find_services_iter(framework=frameworks)

```

## Releasing a new version

To update the package version, edit the `__version__ = ...` string in `dmapiclient/__init__.py`,
commit and push the change and wait for CI to create a new version tag.

Once the tag is available on GitHub, the new version can be used by the apps by adding the following
line to the app `requirements.txt` (replacing `X.Y.Z` with the current version number):

```
git+https://github.com/alphagov/digitalmarketplace-apiclient.git@X.Y.Z#egg=digitalmarketplace-apiclient==X.Y.Z
```

When changing a major version number consider adding a record to the `CHANGELOG.md` with a
description of the change and an example of the upgrade process for the client apps.
