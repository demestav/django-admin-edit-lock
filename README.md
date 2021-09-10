# django-admin-edit-lock

> :warning: Correct operation relies on cache. Therefore, the current version will be unreliable in cases where the default local-memory cache backend is used, along with multiple application server worker (see https://github.com/demestav/django-admin-edit-lock/issues/1).

## Setup
Install package using `pip`:

```shell
python -m pip install django-admin-edit-lock
```

Add it to the installed apps:
```python
INSTALLED_APPS = [
    ...
    "admin_edit_lock",
    ...
]
```

## Configuration
There are two one mandatory settings:

### `ADMIN_EDIT_LOCK_DURATION` 
Defines how long each edit lock should last. The value is in seconds. For example:

```python
ADMIN_EDIT_LOCK_DURATION = 60
```

will keep the lock for sixty seconds.

The lock is being updated regularly (every 5 seconds) as long as the user is still editing the object. Therefore this value needs to be larger than 5 seconds. This configuration will probably be removed in the future, as it does not really offer any value by being user-configurable. The only case this affects the user is how long the lock will remain after the user finished editing. For example, the user updated the lock at 10:00:00 (i.e. the lock expires at 10:01:00) and the user exits the edit screen (closer tab or saves or navigates back etc.) at 10:00:10. For the remaining 50 seconds, the lock will be there without any real purpose.

### `ADMIN_EDIT_LOCK_MAX_DURATION`
Defines for how long a user can keep the same lock. The value is in seconds.

This prevents a user to keep the maintain the edit rights of an object indefinitely. This is useful in cases where a user unintentionally keeps the edit screen open and therefore not allowing other users to edit the object.

## Usage
Use the `AdminEditLockMixin` to enable edit lock on a model. 

For example:

```python
# models.py
from django.db import models

class Book(models.Model):
    name = models.CharField(max_length=100)
```

```python
# admin.py
from django.contrib import admin
from admin_edit_lock.admin import AdminEditLockMixin


class BookAdmin(AdminEditLockMixin, admin.ModelAdmin):
    class Meta:
        model = Book
```

## Roadmap
- Customize messages
- ~~Extending the lock expiry time through AJAX call~~
- ~~Optionally set a limit to how much the lock can be extended~~

## Acknowledgements
This project is inspired by https://github.com/jonasundderwolf/django-admin-locking . This project differentiates by utilizing the Django permissions to decide whether a user can edit or not. Further, this project uses the messages middleware to notify the users of the lock status.
