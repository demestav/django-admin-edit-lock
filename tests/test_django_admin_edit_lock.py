from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from freezegun import freeze_time
import datetime

from tests.models import Book, BookAdmin
from django.contrib.messages.storage import default_storage

import pytest


def test_cahce():
    with freeze_time("2015-10-21 04:29") as frozen_datetime:
        cache.set("testkey", "testvalue", 10)
        assert cache.get("testkey") == "testvalue"
        frozen_datetime.tick(datetime.timedelta(seconds=5))
        assert cache.get("testkey") == "testvalue"
        frozen_datetime.tick(datetime.timedelta(seconds=6))
        assert cache.get("testkey") is None
        assert cache.get("invalid_key") is None


def test_has_change_permission(rf, admin_user):
    """
    has_change_permission returns True for users who can edit objects and
    False for users who can't.
    """
    book_obj = Book.objects.create(name="A Brief History of Timez")
    book_admin = BookAdmin(Book, AdminSite())
    editor = get_user_model().objects.create_user("editor1")
    second_editor = get_user_model().objects.create_user("second_editor1")
    p = Permission.objects.get(codename="change_book")
    editor.user_permissions.add(p)
    second_editor.user_permissions.add(p)

    request = rf.get("")
    request.user = editor
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request._messages = default_storage(request)
    request.session.save()
    assert book_admin.has_change_permission(request, obj=book_obj) is True
    cache.clear()


@pytest.mark.django_db
def test_decline_edit(rf):
    """
    has_change_permission returns False if the edit is locked
    by another user.
    """
    book_obj = Book.objects.create(name="A Brief History of Time")
    book_admin = BookAdmin(Book, AdminSite())
    editor = get_user_model().objects.create_user("editor")
    second_editor = get_user_model().objects.create_user("second_editor")
    p = Permission.objects.get(codename="change_book")
    editor.user_permissions.add(p)
    second_editor.user_permissions.add(p)
    # First editor has edit rights
    request = rf.get("")
    request.user = editor
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    request._messages = default_storage(request)
    book_admin.has_change_permission(request, obj=book_obj)
    # Second editor is declined edit permission
    request.user = second_editor
    middleware.process_request(request)
    request.session.save()
    assert book_admin.has_change_permission(request, obj=book_obj) is False
    cache.clear()


@pytest.mark.django_db
def test_lock_expiry(rf):
    """
    has_change_permission returns True after the lock expires.
    """
    book_obj = Book.objects.create(name="A Brief History of Time")
    book_admin = BookAdmin(Book, AdminSite())
    editor = get_user_model().objects.create_user("editor")
    second_editor = get_user_model().objects.create_user("second_editor")
    p = Permission.objects.get(codename="change_book")
    editor.user_permissions.add(p)
    second_editor.user_permissions.add(p)
    # First editor has edit rights
    with freeze_time("2015-10-21 04:29") as frozen_datetime:
        request = rf.get("")
        request.user = editor
        middleware = SessionMiddleware()
        middleware.process_request(request)
        request.session.save()
        request._messages = default_storage(request)
        book_admin.has_change_permission(request, obj=book_obj)
        # Second editor is declined edit permission
        request = rf.get("")
        frozen_datetime.tick(datetime.timedelta(seconds=5))
        request.user = second_editor
        middleware.process_request(request)
        request.session.save()
        request._messages = default_storage(request)
        assert book_admin.has_change_permission(request, obj=book_obj) is False
        # Second editor is declined edit permission
        request = rf.get("")
        frozen_datetime.tick(datetime.timedelta(seconds=10 * 60))
        request.user = second_editor
        middleware.process_request(request)
        request.session.save()
        request._messages = default_storage(request)
        assert book_admin.has_change_permission(request, obj=book_obj) is True
        cache.clear()
