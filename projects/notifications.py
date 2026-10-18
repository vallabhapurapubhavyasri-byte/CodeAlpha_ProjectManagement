from .models import Notification
from django.urls import reverse


def create_notification(recipient, actor, verb, project=None, task=None, link=""):
    """
    Helper function to safely create notifications.
    Do not notify a user about their own actions.
    """
    if not recipient or recipient == actor:
        return None

    if not link:
        if task:
            link = reverse('task_detail', args=[task.id])
        elif project:
            link = reverse('project_detail', args=[project.id])

    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        verb=verb,
        project=project,
        task=task,
        link=link
    )
