# Digital Marketplace API clients changelog

Records breaking changes from major version bumps

## 10.0.0

PR: [#90](https://github.com/alphagov/digitalmarketplace-apiclient/pull/90)

Removes an unused parameter from the get_direct_award_project endpint.

Old
```python
data_api_client.get_direct_award_project(user_id=123, project_id=123)
```

New
```python
data_api_client.get_direct_award_project(project_id=123)
```


## 9.0.0

PR: [#86](https://github.com/alphagov/digitalmarketplace-apiclient/pull/86)

Remove the default index from the Search API Client; it is now a required argument.

### Example app cange

Old
```python
search_api_client.search_services(q='hosting')
```

New
```python
search_api_client.search_services(index='g-cloud-9', q='hosting')
```

## 8.0.0

PR: [#62](https://github.com/alphagov/digitalmarketplace-apiclient/pull/62)

### What changed

Removed `import_supplier` and `import_service` methods.

These routes have been around since G6, when we were importing a bunch of complete suppliers and their related services. As they were all production-ready (they already had IDs and everything) we just needed a way to create a new object from a JSON blob.

New services created through the app must start out as drafts, and for both services and suppliers IDs are assigned at creation time. This is what we are doing now and will continue doing going forward.

Technically this a breaking change because we are removing functionality, but IRL there were only two scripts using them and those are being deleted.

### Example app change

Old
```python
# import suppler
api_client.import_supplier(1, {"supplier": "data"})


# import service
api_client.import_service(1, {"service": "data"}, "paul@paul.paul")
```

New

You can't do this any more.


## 7.0.0

PR: [#45](https://github.com/alphagov/digitalmarketplace-apiclient/pull/45)

### What changed

Removed `temp_script_countersign_agreement` method.

This route, which allowed the timestamp for countersigning an agreement to be arbitrarily set, only existed for a
one-off script that has now been run on production.

### Example app change

Old
```python
api_client.temp_script_countersign_agreement(framework_agreement_id, countersigned_path, countersigned_at, user)
```

New

You can't do this any more.

## 6.0.0

PR: [#31](https://github.com/alphagov/digitalmarketplace-apiclient/pull/31)

### What changed

Removed `update_brief_status` method.

This functionality has been removed and calls to publish a brief (i.e. change it's status from
'draft' to 'live') should now use the `publish_brief` method. There should no other current
uses of the `update_brief_status` in our apps that set a status to something other than 'live'.

### Example app change

Old
```python
api_client.update_brief_status(brief_id, 'live', user)
```

New
```python
api_client.publish_brief(brief_id, user)
```

## 5.0.0

PR: [#28](https://github.com/alphagov/digitalmarketplace-apiclient/pull/28)

### What changed

Changed `register_framework_agreement_returned` from taking an optional `agreement_details`
parameter to taking an optional `uploader_user_id` parameter. This is because when returning an
agreement (that has a framework agreement version), we expect only an `uploader_user_id` instead
of a flexible dictionary and have made this method stricter to enforce/strongly encourage this.

At the moment, this should cause no actual breaks in our applications as the `agreement_details`
parameter is not yet being used.

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
```python
user = api_client.authenticate_user("email_address", "password", supplier=False)
```

New
```python
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
```python
from dmutils.apiclient import SearchAPIClient
from dmutils.apiclient.base import BaseAPIClient
from dmutils.audit import AuditTypes
```

New
```python
from dmapiclient import SearchAPIClient
from dmapiclient.base import BaseAPIClient
from dmapiclient.audit import AuditTypes
```
