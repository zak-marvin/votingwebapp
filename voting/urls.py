from django.urls import path
from django.urls import path
from . import views
urlpatterns=[path("statistics/", views.admin_statistics_page, name="admin_statistics"),
    path("statistics/data/", views.admin_statistics_data, name="admin_statistics_data"),
]