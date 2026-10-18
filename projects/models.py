from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError


class Project(models.Model):
    STATUS_CHOICES = (
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
    )

    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def is_member(self, user):
        """Check if a user is either the owner or an active member of this project."""
        if not user or not user.is_authenticated:
            return False
        if self.owner_id == user.id:
            return True
        return self.memberships.filter(user=user).exists()

    def is_owner(self, user):
        return user and user.is_authenticated and self.owner_id == user.id

    def can_manage(self, user):
        """Owner or Admin can edit project details, add/remove members, or delete tasks."""
        if not user or not user.is_authenticated:
            return False
        if self.owner_id == user.id:
            return True
        return self.memberships.filter(user=user, role='admin').exists()

    def get_user_role(self, user):
        """Return human-readable role for user in this project."""
        if not user or not user.is_authenticated:
            return None
        if self.owner_id == user.id:
            return 'Owner'
        membership = self.memberships.filter(user=user).first()
        if membership:
            return membership.get_role_display()
        return None

    def get_all_members_query(self):
        """Return QuerySet of all Users who can be assigned to tasks (owner + members)."""
        member_user_ids = list(self.memberships.values_list('user_id', flat=True))
        member_user_ids.append(self.owner_id)
        return User.objects.filter(id__in=set(member_user_ids))

    @property
    def total_tasks_count(self):
        return self.tasks.count()

    @property
    def completed_tasks_count(self):
        return self.tasks.filter(status='completed').count()

    @property
    def progress_percentage(self):
        total = self.total_tasks_count
        if total == 0:
            return 0
        return int((self.completed_tasks_count / total) * 100)


class ProjectMember(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Project Admin'),
        ('member', 'Team Member'),
        ('viewer', 'Viewer'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) in {self.project.title}"


class Task(models.Model):
    STATUS_CHOICES = (
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.project.title})"

    def clean(self):
        super().clean()
        if self.assignee and self.project_id:
            # Assignee must be owner or active member of project
            if not self.project.is_member(self.assignee):
                raise ValidationError(
                    f"User '{self.assignee.username}' is not a member of project '{self.project.title}'."
                )

    @property
    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return self.due_date < timezone.now().date()
        return False

    @property
    def is_due_soon(self):
        """Returns True if due within the next 3 days and not completed."""
        if self.due_date and self.status != 'completed':
            today = timezone.now().date()
            diff = (self.due_date - today).days
            return 0 <= diff <= 3
        return False

    @property
    def comment_count(self):
        return self.comments.count()


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='triggered_notifications'
    )
    verb = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.verb}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    job_title = models.CharField(max_length=100, blank=True)
    bio = models.TextField(blank=True)
    avatar_color = models.CharField(max_length=20, default='#2563EB')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def initials(self):
        name = self.user.get_full_name() or self.user.username
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[1][0]}".upper()
        return name[:2].upper()
