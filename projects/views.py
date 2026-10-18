import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import Project, ProjectMember, Task, TaskComment, Notification, UserProfile
from .forms import (
    UserRegisterForm, UserProfileForm, ProjectForm, ProjectMemberAddForm,
    TaskForm, TaskCommentForm
)
from .notifications import create_notification


def landing_view(request):
    """Public landing page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'projects/landing.html')


def register_view(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Update profile extra fields
            job_title = form.cleaned_data.get('job_title', '')
            if hasattr(user, 'profile'):
                user.profile.job_title = job_title
                user.profile.save()

            login(request, user)
            messages.success(request, f"Welcome to TaskFlow, {user.first_name or user.username}! Your account has been created.")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below to create your account.")
    else:
        form = UserRegisterForm()

    return render(request, 'projects/register.html', {'form': form})


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next') or request.POST.get('next')
                if next_url and next_url.startswith('/'):
                    return redirect(next_url)
                return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, 'projects/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, "You have been logged out safely.")
    return redirect('landing')


@login_required
def profile_view(request):
    """User profile view & edit."""
    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=user, profile=profile)
        if form.is_valid():
            form.save()
            profile.job_title = form.cleaned_data.get('job_title', '')
            profile.bio = form.cleaned_data.get('bio', '')
            profile.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors in the profile form.")
    else:
        form = UserProfileForm(instance=user, profile=profile)

    user_stats = {
        'owned_projects': Project.objects.filter(owner=user).count(),
        'member_projects': Project.objects.filter(memberships__user=user).count(),
        'assigned_tasks': Task.objects.filter(assignee=user).count(),
        'completed_tasks': Task.objects.filter(assignee=user, status='completed').count(),
    }

    return render(request, 'projects/profile.html', {
        'form': form,
        'profile': profile,
        'user_stats': user_stats
    })


@login_required
def dashboard_view(request):
    """Main dashboard displaying metrics, projects, tasks, and notifications."""
    user = request.user
    today = timezone.now().date()

    # Accessible projects
    accessible_projects = Project.objects.filter(
        Q(owner=user) | Q(memberships__user=user)
    ).distinct()

    total_projects = accessible_projects.count()
    owned_projects_count = Project.objects.filter(owner=user).count()
    member_projects_count = Project.objects.filter(memberships__user=user).exclude(owner=user).count()

    # Tasks assigned to user
    user_tasks = Task.objects.filter(assignee=user)
    total_assigned_tasks = user_tasks.count()
    tasks_todo = user_tasks.filter(status='todo').count()
    tasks_in_progress = user_tasks.filter(status='in_progress').count()
    tasks_completed = user_tasks.filter(status='completed').count()

    # Deadlines & overdue
    overdue_tasks = user_tasks.filter(due_date__lt=today).exclude(status='completed')
    upcoming_tasks = user_tasks.filter(
        due_date__gte=today, due_date__lte=today + timezone.timedelta(days=7)
    ).exclude(status='completed').order_by('due_date')[:5]

    # Recently updated projects
    recent_projects = accessible_projects.order_by('-updated_at')[:4]

    # Recent notifications
    recent_notifications = Notification.objects.filter(recipient=user).order_by('-created_at')[:5]

    context = {
        'total_projects': total_projects,
        'owned_projects_count': owned_projects_count,
        'member_projects_count': member_projects_count,
        'total_assigned_tasks': total_assigned_tasks,
        'tasks_todo': tasks_todo,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
        'overdue_count': overdue_tasks.count(),
        'upcoming_tasks': upcoming_tasks,
        'recent_projects': recent_projects,
        'recent_notifications': recent_notifications,
    }
    return render(request, 'projects/dashboard.html', context)


# ==============================================================================
# PROJECT VIEWS
# ==============================================================================

@login_required
def project_list_view(request):
    """List all projects user has access to with search and filters."""
    user = request.user
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    scope = request.GET.get('scope', 'all').strip()

    projects = Project.objects.filter(
        Q(owner=user) | Q(memberships__user=user)
    ).distinct()

    if scope == 'owned':
        projects = projects.filter(owner=user)
    elif scope == 'member':
        projects = projects.filter(memberships__user=user).exclude(owner=user)

    if query:
        projects = projects.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if status_filter:
        projects = projects.filter(status=status_filter)

    projects = projects.annotate(
        task_total=Count('tasks', distinct=True)
    ).order_by('-updated_at')

    context = {
        'projects': projects,
        'query': query,
        'status_filter': status_filter,
        'scope': scope,
        'STATUS_CHOICES': Project.STATUS_CHOICES,
    }
    return render(request, 'projects/project_list.html', context)


@login_required
def project_create_view(request):
    """Create a new group project."""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, f"Project '{project.title}' created successfully!")
            return redirect('project_board', project_id=project.id)
        else:
            messages.error(request, "Failed to create project. Please verify inputs.")
    else:
        form = ProjectForm()

    return render(request, 'projects/project_form.html', {
        'form': form,
        'action': 'Create'
    })


@login_required
def project_detail_view(request, project_id):
    """View project details, team members, and task summary."""
    user = request.user
    project = get_object_or_404(Project, id=project_id)

    if not project.is_member(user):
        messages.error(request, "You do not have access to view this project.")
        return redirect('project_list')

    memberships = project.memberships.select_related('user', 'user__profile').all()
    recent_tasks = project.tasks.select_related('assignee', 'creator').order_by('-created_at')[:8]

    context = {
        'project': project,
        'memberships': memberships,
        'recent_tasks': recent_tasks,
        'is_owner': project.is_owner(user),
        'can_manage': project.can_manage(user),
        'user_role': project.get_user_role(user),
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
def project_edit_view(request, project_id):
    """Edit project title, description, or status."""
    project = get_object_or_404(Project, id=project_id)

    if not project.can_manage(request.user):
        messages.error(request, "Only project owners or administrators can edit project settings.")
        return redirect('project_detail', project_id=project.id)

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f"Project '{project.title}' updated successfully.")
            return redirect('project_detail', project_id=project.id)
        else:
            messages.error(request, "Failed to update project. Please verify inputs.")
    else:
        form = ProjectForm(instance=project)

    return render(request, 'projects/project_form.html', {
        'form': form,
        'project': project,
        'action': 'Edit'
    })


@login_required
def project_delete_view(request, project_id):
    """Delete a project (Owner only)."""
    project = get_object_or_404(Project, id=project_id)

    if not project.is_owner(request.user):
        messages.error(request, "Only the project owner can delete this project.")
        return redirect('project_detail', project_id=project.id)

    if request.method == 'POST':
        title = project.title
        project.delete()
        messages.success(request, f"Project '{title}' and all its tasks were deleted successfully.")
        return redirect('project_list')

    return render(request, 'projects/project_confirm_delete.html', {'project': project})


# ==============================================================================
# PROJECT MEMBERS MANAGEMENT
# ==============================================================================

@login_required
def project_members_view(request, project_id):
    """Manage team members and roles for a project."""
    project = get_object_or_404(Project, id=project_id)

    if not project.is_member(request.user):
        messages.error(request, "You do not have permission to view members of this project.")
        return redirect('project_list')

    can_manage = project.can_manage(request.user)

    if request.method == 'POST' and can_manage:
        form = ProjectMemberAddForm(project, request.POST)
        if form.is_valid():
            new_user = form.cleaned_data['user']
            role = form.cleaned_data['role']
            membership = ProjectMember.objects.create(
                project=project,
                user=new_user,
                role=role
            )
            create_notification(
                recipient=new_user,
                actor=request.user,
                verb=f"added you to project '{project.title}' as {membership.get_role_display()}",
                project=project
            )
            messages.success(request, f"{new_user.username} was added to the project as {membership.get_role_display()}.")
            return redirect('project_members', project_id=project.id)
        else:
            messages.error(request, "Failed to add member. Please select a valid user.")
    else:
        form = ProjectMemberAddForm(project) if can_manage else None

    memberships = project.memberships.select_related('user', 'user__profile').all()

    context = {
        'project': project,
        'memberships': memberships,
        'form': form,
        'can_manage': can_manage,
        'is_owner': project.is_owner(request.user),
    }
    return render(request, 'projects/project_members.html', context)


@login_required
@require_POST
def project_member_remove_view(request, project_id, member_id):
    """Remove a member from a project."""
    project = get_object_or_404(Project, id=project_id)

    if not project.can_manage(request.user):
        messages.error(request, "Only project owners or administrators can remove members.")
        return redirect('project_members', project_id=project.id)

    membership = get_object_or_404(ProjectMember, id=member_id, project=project)
    removed_user = membership.user

    # Unassign tasks currently assigned to this removed member in this project
    project.tasks.filter(assignee=removed_user).update(assignee=None)

    membership.delete()

    create_notification(
        recipient=removed_user,
        actor=request.user,
        verb=f"removed you from project '{project.title}'",
        project=None
    )

    messages.success(request, f"{removed_user.username} has been removed from '{project.title}'.")
    return redirect('project_members', project_id=project.id)


# ==============================================================================
# KANBAN BOARD & TASK DRAG-AND-DROP API
# ==============================================================================

@login_required
def project_board_view(request, project_id):
    """Kanban board view with To Do, In Progress, and Completed columns."""
    user = request.user
    project = get_object_or_404(Project, id=project_id)

    if not project.is_member(user):
        messages.error(request, "You do not have permission to access this project board.")
        return redirect('project_list')

    # Filtering parameters
    assignee_id = request.GET.get('assignee', '').strip()
    priority = request.GET.get('priority', '').strip()
    query = request.GET.get('q', '').strip()

    tasks_qs = project.tasks.select_related('assignee', 'creator').prefetch_related('comments').all()

    if assignee_id:
        if assignee_id == 'unassigned':
            tasks_qs = tasks_qs.filter(assignee__isnull=True)
        else:
            tasks_qs = tasks_qs.filter(assignee_id=assignee_id)

    if priority:
        tasks_qs = tasks_qs.filter(priority=priority)

    if query:
        tasks_qs = tasks_qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    todo_tasks = [t for t in tasks_qs if t.status == 'todo']
    in_progress_tasks = [t for t in tasks_qs if t.status == 'in_progress']
    completed_tasks = [t for t in tasks_qs if t.status == 'completed']

    members = project.get_all_members_query().order_by('username')
    quick_task_form = TaskForm(project)

    context = {
        'project': project,
        'todo_tasks': todo_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
        'members': members,
        'quick_task_form': quick_task_form,
        'filter_assignee': assignee_id,
        'filter_priority': priority,
        'filter_query': query,
        'PRIORITY_CHOICES': Task.PRIORITY_CHOICES,
        'can_manage': project.can_manage(user),
    }
    return render(request, 'projects/project_board.html', context)


@login_required
@require_POST
def task_move_api(request, task_id):
    """
    AJAX endpoint to update task status from Kanban drag-and-drop or select dropdown.
    Supports JSON request body and standard form-encoded POST.
    """
    task = get_object_or_404(Task, id=task_id)

    if not task.project.is_member(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    new_status = None
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
        except Exception:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    else:
        new_status = request.POST.get('status')

    valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
    if new_status not in valid_statuses:
        return JsonResponse({'error': f'Invalid status: {new_status}'}, status=400)

    old_status = task.status
    if old_status != new_status:
        task.status = new_status
        task.save(update_fields=['status', 'updated_at'])

        # Notify assignee if different from current user
        if task.assignee and task.assignee != request.user:
            create_notification(
                recipient=task.assignee,
                actor=request.user,
                verb=f"updated task '{task.title}' status to '{task.get_status_display()}'",
                project=task.project,
                task=task
            )

    return JsonResponse({
        'success': True,
        'task_id': task.id,
        'status': task.status,
        'status_display': task.get_status_display(),
        'project_progress': task.project.progress_percentage
    })


# ==============================================================================
# TASK CRUD & MY TASKS
# ==============================================================================

@login_required
def task_create_view(request, project_id):
    """Create a new task within a project."""
    project = get_object_or_404(Project, id=project_id)

    if not project.is_member(request.user):
        messages.error(request, "You do not have permission to create tasks in this project.")
        return redirect('project_list')

    if request.method == 'POST':
        form = TaskForm(project, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.creator = request.user
            task.save()

            if task.assignee and task.assignee != request.user:
                create_notification(
                    recipient=task.assignee,
                    actor=request.user,
                    verb=f"assigned you to task '{task.title}' in project '{project.title}'",
                    project=project,
                    task=task
                )

            messages.success(request, f"Task '{task.title}' created successfully!")
            return redirect('project_board', project_id=project.id)
        else:
            messages.error(request, "Failed to create task. Please check the form errors.")
    else:
        initial_status = request.GET.get('status', 'todo')
        form = TaskForm(project, initial={'status': initial_status})

    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': project,
        'action': 'Create'
    })


@login_required
def task_detail_view(request, task_id):
    """View task details and full comments thread."""
    task = get_object_or_404(Task.objects.select_related('project', 'creator', 'assignee'), id=task_id)

    if not task.project.is_member(request.user):
        messages.error(request, "You do not have access to view this task.")
        return redirect('project_list')

    comments = task.comments.select_related('author', 'author__profile').order_by('created_at')
    comment_form = TaskCommentForm()

    can_edit = (
        request.user == task.creator or
        request.user == task.assignee or
        task.project.can_manage(request.user)
    )
    can_delete = (
        request.user == task.creator or
        task.project.can_manage(request.user)
    )

    can_manage = task.project.can_manage(request.user)

    context = {
        'task': task,
        'project': task.project,
        'comments': comments,
        'comment_form': comment_form,
        'can_edit': can_edit,
        'can_delete': can_delete,
        'can_manage': can_manage,
    }
    return render(request, 'projects/task_detail.html', context)


@login_required
def task_edit_view(request, task_id):
    """Edit task details."""
    task = get_object_or_404(Task.objects.select_related('project'), id=task_id)

    can_edit = (
        request.user == task.creator or
        request.user == task.assignee or
        task.project.can_manage(request.user)
    )
    if not can_edit:
        messages.error(request, "You do not have permission to edit this task.")
        return redirect('task_detail', task_id=task.id)

    old_assignee = task.assignee

    if request.method == 'POST':
        form = TaskForm(task.project, request.POST, instance=task)
        if form.is_valid():
            updated_task = form.save()

            # If assignee changed, notify new assignee
            if updated_task.assignee and updated_task.assignee != old_assignee and updated_task.assignee != request.user:
                create_notification(
                    recipient=updated_task.assignee,
                    actor=request.user,
                    verb=f"assigned you to task '{updated_task.title}' in project '{updated_task.project.title}'",
                    project=updated_task.project,
                    task=updated_task
                )

            messages.success(request, f"Task '{updated_task.title}' updated successfully.")
            return redirect('task_detail', task_id=updated_task.id)
        else:
            messages.error(request, "Failed to update task. Please check the form errors.")
    else:
        form = TaskForm(task.project, instance=task)

    return render(request, 'projects/task_form.html', {
        'form': form,
        'project': task.project,
        'task': task,
        'action': 'Edit'
    })


@login_required
def task_delete_view(request, task_id):
    """Delete a task with confirmation."""
    task = get_object_or_404(Task.objects.select_related('project'), id=task_id)

    can_delete = (
        request.user == task.creator or
        task.project.can_manage(request.user)
    )
    if not can_delete:
        messages.error(request, "You do not have permission to delete this task.")
        return redirect('task_detail', task_id=task.id)

    project_id = task.project_id
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f"Task '{title}' has been deleted.")
        return redirect('project_board', project_id=project_id)

    return render(request, 'projects/task_confirm_delete.html', {'task': task})


@login_required
def my_tasks_view(request):
    """All tasks assigned to current user across all projects with filters."""
    user = request.user
    query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    project_filter = request.GET.get('project', '').strip()
    sort = request.GET.get('sort', 'due_date').strip()

    tasks = Task.objects.filter(assignee=user).select_related('project', 'creator')

    if query:
        tasks = tasks.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    if project_filter:
        tasks = tasks.filter(project_id=project_filter)

    if sort == 'due_date':
        tasks = tasks.order_by('due_date', '-created_at')
    elif sort == 'priority':
        tasks = tasks.order_by('-priority', 'due_date')
    elif sort == 'updated':
        tasks = tasks.order_by('-updated_at')
    else:
        tasks = tasks.order_by('-created_at')

    # User's accessible projects for the filter dropdown
    user_projects = Project.objects.filter(
        Q(owner=user) | Q(memberships__user=user)
    ).distinct()

    context = {
        'tasks': tasks,
        'user_projects': user_projects,
        'query': query,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'project_filter': project_filter,
        'sort': sort,
        'STATUS_CHOICES': Task.STATUS_CHOICES,
        'PRIORITY_CHOICES': Task.PRIORITY_CHOICES,
    }
    return render(request, 'projects/my_tasks.html', context)


# ==============================================================================
# COMMENTS
# ==============================================================================

@login_required
@require_POST
def task_comment_add_view(request, task_id):
    """Post a comment on a task."""
    task = get_object_or_404(Task.objects.select_related('project'), id=task_id)

    if not task.project.is_member(request.user):
        messages.error(request, "You cannot comment on tasks in projects you do not belong to.")
        return redirect('project_list')

    form = TaskCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.task = task
        comment.author = request.user
        comment.save()

        # Notify assignee and creator if they are not the comment author
        recipients = set()
        if task.assignee and task.assignee != request.user:
            recipients.add(task.assignee)
        if task.creator and task.creator != request.user:
            recipients.add(task.creator)

        for recipient in recipients:
            create_notification(
                recipient=recipient,
                actor=request.user,
                verb=f"commented on task '{task.title}'",
                project=task.project,
                task=task
            )

        messages.success(request, "Comment posted successfully.")
    else:
        messages.error(request, "Comment cannot be empty.")

    return redirect(f"{reverse('task_detail', args=[task.id])}#comments")


@login_required
@require_POST
def task_comment_delete_view(request, comment_id):
    """Delete a comment (Comment author or project manager only)."""
    comment = get_object_or_404(TaskComment.objects.select_related('task', 'task__project'), id=comment_id)
    task = comment.task

    can_delete = (
        request.user == comment.author or
        task.project.can_manage(request.user)
    )
    if not can_delete:
        messages.error(request, "You do not have permission to delete this comment.")
        return redirect('task_detail', task_id=task.id)

    comment.delete()
    messages.success(request, "Comment removed.")
    return redirect('task_detail', task_id=task.id)


# ==============================================================================
# NOTIFICATIONS (BONUS FEATURE)
# ==============================================================================

@login_required
def notifications_list_view(request):
    """Full notifications list view."""
    user = request.user
    filter_type = request.GET.get('filter', 'all')

    notifications_qs = Notification.objects.filter(recipient=user).select_related('actor', 'project', 'task')

    if filter_type == 'unread':
        notifications_qs = notifications_qs.filter(is_read=False)

    paginator = Paginator(notifications_qs, 15)
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)

    unread_count = Notification.objects.filter(recipient=user, is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'filter_type': filter_type,
    }
    return render(request, 'projects/notifications.html', context)


@login_required
def notification_mark_read_view(request, notification_id):
    """Mark a notification as read and redirect to its link or return JSON."""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return JsonResponse({'success': True, 'unread_count': unread_count})

    if notification.link:
        return redirect(notification.link)
    return redirect('notifications_list')


@login_required
@require_POST
def notification_mark_all_read_view(request):
    """Mark all notifications as read for current user."""
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notifications_list')


@login_required
def notification_count_api(request):
    """Lightweight API endpoint for polling unread count."""
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'unread_count': count})


# ==============================================================================
# GLOBAL SEARCH
# ==============================================================================

@login_required
def search_view(request):
    """Global search across projects and tasks accessible to the user."""
    query = request.GET.get('q', '').strip()
    user = request.user

    matching_projects = []
    matching_tasks = []

    if query:
        # Search accessible projects
        accessible_projects = Project.objects.filter(
            Q(owner=user) | Q(memberships__user=user)
        ).distinct()
        matching_projects = accessible_projects.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

        # Search tasks in accessible projects
        matching_tasks = Task.objects.filter(
            project__in=accessible_projects
        ).filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).select_related('project', 'assignee')

    context = {
        'query': query,
        'matching_projects': matching_projects,
        'matching_tasks': matching_tasks,
        'total_results': (len(matching_projects) if query else 0) + (len(matching_tasks) if query else 0),
    }
    return render(request, 'projects/search.html', context)
