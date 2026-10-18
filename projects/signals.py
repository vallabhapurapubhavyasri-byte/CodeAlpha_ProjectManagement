from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
import random

AVATAR_COLORS = [
    '#2563EB', '#7C3AED', '#DB2777', '#EA580C',
    '#059669', '#0891B2', '#4F46E5', '#9333EA',
    '#0D9488', '#D97706', '#E11D48', '#475569'
]

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        color = random.choice(AVATAR_COLORS)
        UserProfile.objects.create(user=instance, avatar_color=color)
    else:
        if not hasattr(instance, 'profile'):
            color = random.choice(AVATAR_COLORS)
            UserProfile.objects.create(user=instance, avatar_color=color)
