# Digital Marketplace API clients changelog

Records breaking changes from major version bumps

## 4.0.0

PR: [#26](https://github.com/alphagov/digitalmarketplace-apiclient/pull/26)

### What changed

Removed the `unset_framework_agreement_returned` method.

This shouldn't require any changes as this method is only used in at most one old script and should 
never need to be used again.

## 3.0.0

PR: [#14](https://github.com/alphagov/digitalmarketplace-apiclient/pull/14)

### What changed

All POST, PUT and DELETE methods are now sending `"updated_by"` payload instead of `"update_details"`.
The new payload should be supported by the data API for all methods.

This shouldn't require any changes to the code that's using `DataAPIClient`, but might break test
expectations if any of them rely on `update_details` payload key.

### Example app change

Search for `update_details` and replace all instances of `{"update_details": {"updated_by": ...}}` with
`{"updated_by": ...}` if they affect the tests.

## 2.0.0

PR: [#8](https://github.com/alphagov/digitalmarketplace-apiclient/pull/8)

### What changed

The `authenticate_user` method used to take a boolean flag to indicate if the user is a supplier user.
Now it just returns users with any role, and it is up to the front-end apps to decide if the authenticated
user should be allowed to access a resource.

### Example app change

Old
```
user = api_client.authenticate_user("email_address", "password", supplier=False)
```

New
```
user = api_client.authenticate_user("email_address", "password")
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
