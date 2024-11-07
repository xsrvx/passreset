"""passreset URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
# passreset/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings  # Import settings
from django.conf.urls.static import static  # Import static function
from .views import custom_login, home_view, search_users, generate_password_view, generate_and_change_password_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', custom_login, name='login'),
    path('search/<str:query>/', search_users, name='search_users'),
    path('', home_view, name='home'),
    path('generate_password/', generate_password_view, name='generate_password'),
    path('generate_and_change_password/<str:username>/<path:user_dn>/', generate_and_change_password_view, name='generate_and_change_password'),
   # Other URL patterns...
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
