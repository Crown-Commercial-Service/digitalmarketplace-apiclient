# Digital Marketplace API clients changelog

Records breaking changes from major version bumps

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
