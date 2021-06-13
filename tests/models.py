from django.db import models
from django.contrib import admin
from admin_edit_lock.admin import AdminEditLockMixin


class Book(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class BookAdmin(AdminEditLockMixin, admin.ModelAdmin):
    class Meta:
        model = Book
