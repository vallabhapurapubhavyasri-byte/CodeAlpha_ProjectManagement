from django.urls import path
from . import views

urlpatterns = [
    # Public & Auth
    path('', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Projects
    path('projects/', views.project_list_view, name='project_list'),
    path('projects/new/', views.project_create_view, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.project_edit_view, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete_view, name='project_delete'),
    path('projects/<int:project_id>/members/', views.project_members_view, name='project_members'),
    path('projects/<int:project_id>/members/<int:member_id>/remove/', views.project_member_remove_view, name='project_member_remove'),
    path('projects/<int:project_id>/board/', views.project_board_view, name='project_board'),

    # Tasks
    path('projects/<int:project_id>/tasks/new/', views.task_create_view, name='task_create'),
    path('tasks/<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('tasks/<int:task_id>/edit/', views.task_edit_view, name='task_edit'),
    path('tasks/<int:task_id>/delete/', views.task_delete_view, name='task_delete'),
    path('tasks/<int:task_id>/move/', views.task_move_api, name='task_move_api'),
    path('my-tasks/', views.my_tasks_view, name='my_tasks'),

    # Comments
    path('tasks/<int:task_id>/comments/add/', views.task_comment_add_view, name='task_comment_add'),
    path('comments/<int:comment_id>/delete/', views.task_comment_delete_view, name='task_comment_delete'),

    # Notifications
    path('notifications/', views.notifications_list_view, name='notifications_list'),
    path('notifications/<int:notification_id>/read/', views.notification_mark_read_view, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notification_mark_all_read_view, name='notification_mark_all_read'),
    path('api/notifications/count/', views.notification_count_api, name='notification_count_api'),

    # Search
    path('search/', views.search_view, name='search'),
]
