from .models import Book
from django.contrib import admin
from admin_edit_lock.admin import AdminEditLockMixin


class BookAdmin(AdminEditLockMixin, admin.ModelAdmin):
    class Meta:
        model = Book


admin.site.register(Book, BookAdmin)
