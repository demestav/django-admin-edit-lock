import datetime

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.messages.storage import default_storage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import cache
from django.urls import reverse
from freezegun import freeze_time

from tests.models import Book, BookAdmin


def dummy_get_response(request):
    return None


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
    middleware = SessionMiddleware(dummy_get_response)
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
    middleware = SessionMiddleware(dummy_get_response)
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
        middleware = SessionMiddleware(dummy_get_response)
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
        # Second editor is allow edit permission
        request = rf.get("")
        frozen_datetime.tick(datetime.timedelta(seconds=10 * 60))
        request.user = second_editor
        middleware.process_request(request)
        request.session.save()
        request._messages = default_storage(request)
        assert book_admin.has_change_permission(request, obj=book_obj) is True
        cache.clear()


@pytest.mark.django_db
def test_update_lock_no_change_permission(client):
    """
    Return request Forbidden if the user is not allowed to change by default.
    """
    book_obj = Book.objects.create(name="A Brief History of Time")
    get_user_model().objects.create_user(
        username="editor", password="123", is_staff=True
    )
    url = reverse("admin:tests_book_change", args=(book_obj.id,))
    client.login(username="editor", password="123")
    response = client.post(url + "update-lock/")
    assert response.status_code == 403
    cache.clear()


@pytest.mark.django_db
def test_update_lock_no_previous_lock(client):
    """
    Return request Forbidden if the user did not obtain a lock previously.
    """
    book_obj = Book.objects.create(name="A Brief History of Time")
    editor = get_user_model().objects.create_user(
        username="editor", password="123", is_staff=True
    )
    p = Permission.objects.get(codename="change_book")
    editor.user_permissions.add(p)
    url = reverse("admin:tests_book_change", args=(book_obj.id,))
    client.login(username="editor", password="123")
    response = client.post(url + "update-lock/")
    assert response.status_code == 403
    cache.clear()


@pytest.mark.django_db
def test_update_lock_does_not_own_lock(client):
    """
    Return request Forbidden if users try to update a lock they don't own.
    """
    Book.objects.create(name="A Brief History of Time")
    editor = get_user_model().objects.create_user(
        username="editor", password="123", is_staff=True
    )
    second_editor = get_user_model().objects.create_user(
        username="second_editor", password="123", is_staff=True
    )
    p = Permission.objects.get(codename="change_book")
    editor.user_permissions.add(p)
    second_editor.user_permissions.add(p)
    url = reverse("admin:tests_book_change", args=(1,))
    client.login(username="editor", password="123")
    client.get(url)
    client.login(username="second_editor", password="123")
    response = client.post(url + "update-lock/")
    assert response.status_code == 403
    cache.clear()


@pytest.mark.django_db
def test_update_lock_max_lock_duration(client, settings):
    """
    Lock should not be updated beyond the duration set by
    ADMIN_EDIT_LOCK_DURATION
    """
    settings.ADMIN_EDIT_LOCK_DURATION = 20
    settings.ADMIN_EDIT_LOCK_MAX_DURATION = 30

    book_obj = Book.objects.create(name="A Brief History of Time")
    editor = get_user_model().objects.create_user(
        username="editor", password="123", is_staff=True
    )
    p = Permission.objects.get(codename="change_book")
    editor.user_permissions.add(p)
    url = reverse("admin:tests_book_change", args=(book_obj.id,))
    client.login(username="editor", password="123")
    with freeze_time("2015-10-21 04:29") as frozen_datetime:
        # Get the initial lock
        response = client.get(url)
        assert response.status_code == 200
        # Update the lock
        frozen_datetime.tick(datetime.timedelta(seconds=19))
        response = client.post(url + "update-lock/")
        assert response.status_code == 204
        # Check that lock was updated only for 11 seconds
        ttl = cache._expire_info.get(":1:admin-edit-lock-tests-Book-1")
        expiry_seconds = (
            datetime.datetime.fromtimestamp(ttl) - frozen_datetime()
        ).seconds
        assert expiry_seconds == 11
    cache.clear()
