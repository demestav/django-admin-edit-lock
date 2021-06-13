from django.core.cache import cache
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages


class AdminEditLockMixin:
    def notify_user(self, request, message):
        """Add message only if it does not already exist."""
        if message not in [m.message for m in messages.get_messages(request)]:
            messages.warning(request, message)

    def has_change_permission(self, request, obj=None):
        default_permission = super().has_change_permission(request, obj)
        session_key = request.session.session_key

        if obj and default_permission:
            cache_key = "admin-edit-lock-%s-%s-%s" % (
                obj._meta.app_label,
                obj.__class__.__name__,
                obj.id,
            )

            cache_session_key = cache.get(cache_key)
            if cache_session_key:
                if cache_session_key != session_key:
                    lock_permission = False
                else:
                    lock_permission = True
            else:
                cache.set(cache_key, session_key, settings.ADMIN_EDIT_LOCK_DURATION)
                cache_session_key = cache.get(cache_key)
                lock_permission = True

            if lock_permission is True:
                self.notify_user(
                    request,
                    _(
                        "This is currently edited by you. Other users can edit once you finish editing."
                    ),
                )
            elif lock_permission is False:
                self.notify_user(
                    request,
                    _(
                        "This is currently being edited by someone else. Editing disabled."
                    ),
                )

            return lock_permission
        return default_permission
