from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import VoterToken, ManagerToken, Vote


@admin.register(VoterToken)
class VoterTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "token_hash", "is_active")
    list_filter = ("is_active",)


@admin.register(ManagerToken)
class ManagerTokenAdmin(admin.ModelAdmin):
    list_display = ("id", "candidate", "is_active")
    list_filter = ("is_active",)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ("id", "position", "candidate", "created_at")
    list_filter = ("position",)