from django import template

register = template.Library()

@register.filter(name='user_role')
def user_role(project, user):
    """Returns the role of user in project."""
    if not project or not user:
        return 'Member'
    return project.get_user_role(user) or 'Member'

@register.filter(name='is_owner')
def is_owner(project, user):
    if not project or not user:
        return False
    return project.is_owner(user)

@register.filter(name='can_manage')
def can_manage(project, user):
    if not project or not user:
        return False
    return project.can_manage(user)
