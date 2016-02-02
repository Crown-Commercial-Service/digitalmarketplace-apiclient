# Digital Marketplace API clients changelog

Records breaking changes from major version bumps

## 2.0.0

PR: [#7](https://github.com/alphagov/digitalmarketplace-apiclient/pull/7)

### What changed

The `authenticate_user` method used to take a boolen flag to indicate if the user is a supplier user.
It now takes a `role` parameter instead, and only returns the user if the role matches the specified 
role of the retrieved user.

### Example app change

Old
```
user = api_client.authenticate_user("email_address", "password", supplier=False)
```

New
```
user = api_client.authenticate_user("email_address", "password", role='buyer')
```

## 1.0.0

PR: [#1](https://github.com/alphagov/digitalmarketplace-apiclient/pull/1)

### What changed

Initial import from digitalmarketplace-utils. Compared to the latest utils version
the package name is now changed from `dmutils.apiclient` to `dmapiclient` and
audit module was moved from `dmutils.audit` to `dmapiclient.audit`.

Main package imports (ie `from dmutils.apiclient import ...`) can be preserved by
`dmutils`, however imports from `dmutils.apiclient.*` modules will have to be
changed to either imports from the main package namespace or the new package name
(eg `from dmapiclient.errors import ...`).

### Example app change

Old
```
from dmutils.apiclient import SearchAPIClient
from dmutils.apiclient.base import BaseAPIClient
from dmutils.audit import AuditTypes
```

New
```
from dmapiclient import SearchAPIClient
from dmapiclient.base import BaseAPIClient
from dmapiclient.audit import AuditTypes
```
