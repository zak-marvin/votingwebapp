"""
URL configuration for secure_voting project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from voting.views import home, vote
from voting.api import stats
from django.conf import settings
from django.conf.urls.static import static
from users.views import login_choice, admin_login, manager_login
from elections.views import admin_dashboard, manager_dashboard
from voting.views import admin_tokens, export_tokens,admin_statistics
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name="home"),
    path('vote/', vote, name="vote"),
    path('api/stats/<int:position_id>/', stats),
    path('login/', login_choice),
path('login/admin/', admin_login),
path('login/manager/', manager_login),
path('dashboard/admin/tokens/', admin_tokens, name="admin_tokens"),
path('dashboard/admin/export/', export_tokens, name="export_tokens"),
path('statistics/', admin_statistics, name="statistics"),
path('dashboard/admin/', admin_dashboard, name="admin_dashboard"),
path('dashboard/manager/', manager_dashboard, name="manager_dashboard"),
path('dashboard/manager/', manager_dashboard, name="manager_dashboard"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)