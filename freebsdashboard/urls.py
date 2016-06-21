from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^set_timezone$', views.set_timezone, name='set_timezone'),
    url(r'^zfs_snapshots/', include('ZFSAdmin.urls')),
    url(r'^', include('ZFSAdmin.urls')),
    # authorization urls
    url(r'^password_change/$', auth_views.password_change,
        {'template_name': 'registration/password_change_form.html'}, name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done,
        {'template_name': 'registration/password_change_done.html'}, name='password_change_done'),
    url(r'^password_reset/$', auth_views.password_reset,
        {'template_name': 'registration/password_reset_form.html'}, name='password_reset'),
    url(r'^password_reset/done$', auth_views.password_reset_done,
        {'template_name': 'registration/password_reset_done.html'}, name='password_reset_done'),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm,
        {'template_name': 'registration/password_reset_confirm.html'}, name='password_reset_confirm'),
    url(r'^reset/done$', auth_views.password_reset_complete,
        {'template_name': 'registration/password_reset_complete.html'}, name='password_reset_complete'),
    url(r'^login/$', auth_views.login,
        {'template_name': 'registration/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout,
        {'template_name': 'registration/logged_out.html'}, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
