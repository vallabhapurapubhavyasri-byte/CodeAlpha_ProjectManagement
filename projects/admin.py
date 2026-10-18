from django.contrib import admin
from .models import Project, ProjectMember, Task, TaskComment, Notification, UserProfile


class ProjectMemberInline(admin.TabularInline):
    model = ProjectMember
    extra = 1
    autocomplete_fields = ['user']


class TaskInline(admin.TabularInline):
    model = Task
    extra = 0
    fields = ['title', 'assignee', 'status', 'priority', 'due_date']
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'status', 'total_tasks_count', 'progress_percentage', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'owner']
    search_fields = ['title', 'description', 'owner__username']
    inlines = [ProjectMemberInline, TaskInline]


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'role', 'joined_at']
    list_filter = ['role', 'joined_at']
    search_fields = ['user__username', 'project__title']


class TaskCommentInline(admin.TabularInline):
    model = TaskComment
    extra = 0


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'assignee', 'status', 'priority', 'due_date', 'comment_count', 'created_at']
    list_filter = ['status', 'priority', 'project', 'due_date']
    search_fields = ['title', 'description', 'project__title', 'assignee__username']
    inlines = [TaskCommentInline]


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'task', 'created_at']
    search_fields = ['author__username', 'content', 'task__title']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'actor', 'verb', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['recipient__username', 'verb']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_title', 'avatar_color', 'created_at']
    search_fields = ['user__username', 'job_title', 'bio']
