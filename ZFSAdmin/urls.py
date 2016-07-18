from django.conf.urls import url
from . import views

app_name = 'ZFSAdmin'

urlpatterns = [
	# /
	url(r'^$', views.IndexView.as_view(), name='index'),
	url(r'^task_checker', views.task_checker, name='task_checker'),
	url(r'^take_snapshots$', views.take_snapshots, name='take_snapshots'),
	url(r'^delete_snapshots', views.delete_snapshots, name='delete_snapshots'),
	url(r'^clone_snapshots', views.clone_snapshots, name='clone_snapshots'),
	url(r'^delete_filesystem', views.delete_filesystem, name='delete_filesystem'),
	url(r'^manage_filesystem', views.manage_filesystem, name='manage_filesystem'),
]