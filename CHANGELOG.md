# Digital Marketplace API clients changelog

Records breaking changes from major version bumps

## 22.0.0

Mark this package as PEP 561 compatible. If you have dmapiclient as a dependency and run type checking, the type checker
will now check that you're using dmapiclient correctly. This might break your application's type checking if you're 
using dmapiclient incorrectly.

## 21.0.0

All "attributes" of apiclient instances have been made private and replaced with read-only properties of the same name.
This is to encourage use of apiclients as objects that are unmutated after construction, making their use (hopefully)
threadsafe.

The attributes in question comprise `RETRIES`, `RETRIES_BACKOFF_FACTOR`, `RETRIES_FORCE_STATUS_CODES`, `base_url`,
`auth_token`, `enabled`, `timeout`. It seems unlikely that any code was mutating these values
post-construction/`init_app`, but it's worth doing a check before upgrading.

## 20.0.0

PR: [#205](https://github.com/alphagov/digitalmarketplace-apiclient/pull/205)

The with_declarations parameter of find_framework_suppliers method of DataAPIClient now defaults to True instead of None. This will increase significantly the size of all replies using it. 

## 19.0.0

PR: [#152](https://github.com/alphagov/digitalmarketplace-apiclient/pull/152)

We're now using urllib3's Retry util to retry failed requests made by the base api client. This has allowed us to
remove backoff from `make_iter_method` and so also remove the package from the api client's dependencies. It also means
that we no longer need `HTTPTemporaryError` so it's been removed.

Anything that uses the api client and has it's own backoff setup (such as some of our scripts)
will need to adjust (or remove) their config to prevent potentially making far too many retry requests.

Anything that uses `HTTPTemporaryError` will need to remove it. The only place I've found it is in a few one off scripts
in the scripts repo for backoff setup.

## 18.0.0

PR: [#151](https://github.com/alphagov/digitalmarketplace-apiclient/pull/151)

The default request error message for unrecognised/unhandled errors has changed from 'Request failed' to 'Unknown request failure in dmapiclient'. 'Request failed' should be seen only in exceptional circumstances - most exceptions raised from failed requests should now hold the str() and repr() calls of the request error as their message.

Any code that relies on the specific format of the request errors raised by the apiclient will need to be updated.

## 17.0.0

PR: [#143](https://github.com/alphagov/digitalmarketplace-apiclient/pull/143)

No longer python2 compatible.

## 16.0.0

PR: [#137](https://github.com/alphagov/digitalmarketplace-apiclient/pull/137)

Moves `api_stubs.py` from this repo (digitalmarketplace-apiclient) to utils (digitalmarketplace-utils). Any repositories using
the stubs need to now use stubs from dm-utils.

Ensure that you update frontend app requirements files to use dmutils>=36.6.0 and that you update imports. The interface for
some of the stubs has changed slightly, and more detailed responses are returned for the frameworks stub, so be aware
of this as you migrate.

Old:
```python
import dmapiclient.api_stubs
```

New:
```python
import dmutils.api_stubs
```


## (14.5.0 ->) 15.0.0

:rotating_light: **Note:** there was mistaken versioning between `14.5.0` and `15.0.0`, meaning that the changes
described below for `15.0.0` actually applied from `14.5.0` onwards.

PR: [#123](https://github.com/alphagov/digitalmarketplace-apiclient/pull/123)

Removes `get_direct_award_project_services_iter` in favour of `find_direct_award_project_services_iter`, which is the
more consistent naming scheme.

Old:
```python
data_api_client.get_direct_award_project_services_iter(...)
```

New:
```python
data_api_client.find_direct_award_project_services_iter(...)
```

## 14.0.0

PR: [#116](https://github.com/alphagov/digitalmarketplace-apiclient/pull/116)

`search_services` method on the search-api-client has been generalized to `search` and now takes a `doc_type` argument.
This allows more than just services to be searched.

`aggregate` method on the search-api-client has been generalized to `aggregate` to allow for aggregating
briefs too. It takes an extra argument, `doc_type`.

Old:
```
search_api_client.aggregate_services(index=index, q=q, aggregations=aggregations)
search_api_client.search_services(index, q=q, page=page, id_only=id_only, **filters)
```

New:
```
search_api_client.aggregate(index=index, doc_type='services', q=q, aggregations=aggregations)
search_api_client.search(index, doc_type, q=q, page=page, id_only=id_only, **filters)
```

## 13.0.0

PR: [#115](https://github.com/alphagov/digitalmarketplace-apiclient/pull/115)

`name` parameter has been added to `update_user` method,  so any code calling
this method with positional parameters needs to be updated to use this version.

## 12.0.0

PR: [#111](https://github.com/alphagov/digitalmarketplace-apiclient/pull/111)

`mapping` parameter is now required for Search API index creation, as we must be
able to distinguish between the 'services' mapping and the forthcoming potential
`briefs` mapping. We might also in future have multiple mappings to cover a new
non-compatible G-Cloud index, for advance preparation of the new index in advance
of the framework going live.

## 11.0.0

PR: [#105](https://github.com/alphagov/digitalmarketplace-apiclient/pull/105)

Gives `user_id` parameter a default for `find_direct_award_project_searches` and `get_direct_award_project_services`,
which changes the order of their positional parameters.

The old/new examples below are calling the methods with no `user_id` and a `project_id` of 123.

Old
```
data_api_client.get_direct_award_project_services(None, 123)
data_api_client.find_direct_award_project_searches(None, 123)
```

New
```
data_api_client.get_direct_award_project_services(123)
data_api_client.find_direct_award_project_searches(123)
```


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
