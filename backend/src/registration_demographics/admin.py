"""
Django admin registration for registration_demographics.

The admin surface is the easiest end-to-end verification path for workshop
participants: register a user, fill in the demographic fields, then confirm
the record at ``/admin/registration_demographics/learnerdemographics/``.
"""

from django.contrib import admin

from .models import LearnerDemographics


@admin.register(LearnerDemographics)
class LearnerDemographicsAdmin(admin.ModelAdmin):
    """Read-mostly admin for LearnerDemographics."""

    list_display = ("user", "pronouns", "department", "modified")
    list_filter = ("department",)
    search_fields = ("user__username", "user__email", "pronouns", "department")
    readonly_fields = ("created", "modified")
    raw_id_fields = ("user",)
    ordering = ("-modified",)
