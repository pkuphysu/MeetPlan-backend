from django.contrib import admin

from apps.pku_auth.models import OpenIDClient


@admin.register(OpenIDClient)
class OpenIDClientAdmin(admin.ModelAdmin):
    list_display = ["client_id", "scopes"]
    ordering = ["-id"]
