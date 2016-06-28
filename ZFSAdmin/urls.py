from django.conf.urls import url
from . import views, hooks

app_name = 'ZFSAdmin'

urlpatterns = [
	# /
	url(r'^$', views.IndexView.as_view(), name='index'),
	url(r'^snapshot_task_manager', views.snapshot_task_manager, name='snapshot_task_manager'),
	url(r'^update_snapshots', views.update_snapshot_list, name='update_snapshots'),
	url(r'^take_snapshot$', views.TakeSnapshotView.as_view(), name='take_snapshot'),
	url(r'^delete_snapshots', views.delete_snapshots, name='delete_snapshots'),
	url(r'^clone_snapshots', views.clone_snapshots, name='clone_snapshots'),
	url(r'^delete_filesystem', views.delete_filesystem, name='delete_filesystem'),
	url(r'^change_filesystems', views.ChangeFileSystems.as_view(), name='change_filesystems'),
]