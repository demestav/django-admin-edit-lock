# django-admin-edit-lock

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
The is one mandatory setting `ADMIN_EDIT_LOCK_DURATION` which defines how long the edit lock should last. The value is in seconds. For example:

```python
ADMIN_EDIT_LOCK_DURATION = 10 * 60
```

will keep the lock for ten minutes.

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
from django.contrib import admin
from admin_edit_lock.admin import AdminEditLockMixin


class BookAdmin(AdminEditLockMixin, admin.ModelAdmin):
    class Meta:
        model = Book
```

## Roadmap
- Customize messages
- Extending the lock expiry time through AJAX call
- Optionally set a limit to how much the lock can be extended

## Acknowledgements
This project is inspired by https://github.com/jonasundderwolf/django-admin-locking . This project differentiates by utilizing the Django permissions to decide whether a user can edit or not. Further, this project uses the messages middleware to notify the users of the lock status.