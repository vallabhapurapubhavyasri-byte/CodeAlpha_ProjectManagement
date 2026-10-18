from .models import Notification, Project
from django.db.models import Q

def global_context(request):
    if not request.user.is_authenticated:
        return {}

    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    accessible_projects = Project.objects.filter(
        Q(owner=request.user) | Q(memberships__user=request.user)
    ).distinct()

    return {
        'nav_unread_notifications_count': unread_count,
        'nav_user_projects': accessible_projects[:6],
        'nav_total_projects_count': accessible_projects.count(),
    }
