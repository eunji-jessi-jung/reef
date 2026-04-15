# Stub Creation Patterns

Patterns for creating dependency stubs during runtime extraction. Used by reef:source Step 2 (Tier 2). Stubs go in a temp directory added to `PYTHONPATH` / `NODE_PATH`. Never modify the source repo. Clean up after extraction.

---

## The Simple Stub

For packages where only top-level import matters:

```python
# <stub-dir>/<package_name>/__init__.py
class _Stub:
    def __init__(self, *a, **kw): pass
    def __getattr__(self, name): return lambda *a, **kw: None
    def __call__(self, *a, **kw): return self

def __getattr__(name):
    return _Stub()
```

## The Comprehensive Stub (for generated API clients, auth libraries)

When the simple stub fails because the code imports specific sub-modules and classes, build a deeper structure. This is common with generated API clients (OpenAPI-generated SDKs):

```
<stub-dir>/
  <package_name>/
    __init__.py                    # module-level __getattr__
    api/
      __init__.py                  # module-level __getattr__
      permissions_api.py           # class PermissionsApi: def __init__(self, api_client=None): pass
      resource_api.py              # class ResourceApi: ...
      user_api.py                  # class UserApi: ...
    models/
      __init__.py                  # module-level __getattr__
    rest.py                        # class RESTResponse: status=200; data=b'{}'
    api_client.py                  # class ApiClient: def __init__(self, configuration=None): ...
    configuration.py               # class Configuration: def __init__(self, host=None): ...
    exceptions.py                  # class ApiException(Exception): pass
    decorators/
      __init__.py
      auth_decorators.py           # see decorator pattern below
```

## Decorator Stub Pattern

When a private package provides decorators used in route definitions:

```python
# decorators/auth_decorators.py
class AuthConfig: pass
class AuthError(Exception): pass

def check_authorization(*args, **kwargs):
    """Return a no-op decorator that preserves the original function."""
    def decorator(fn):
        return fn
    return decorator
```

The key insight: `check_authorization` is used as `@check_authorization(resource=..., action=...)` — it must be a function that returns a decorator, not a plain function. Getting this wrong causes `TypeError: 'NoneType' object is not callable`.
