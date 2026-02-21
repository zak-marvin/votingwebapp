from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Position, Candidate


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "position", "vote_count")
    list_filter = ("position",)
    search_fields = ("name",)