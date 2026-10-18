from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from projects.models import UserProfile


class Command(BaseCommand):
    help = 'Creates a demo superuser administrator (admin / admin1234)'

    def handle(self, *args, **options):
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@taskflow.demo',
                password='admin1234',
                first_name='System',
                last_name='Admin'
            )
            profile, _ = UserProfile.objects.get_or_create(user=admin_user)
            profile.job_title = 'Workspace Administrator'
            profile.save()
            self.stdout.write(self.style.SUCCESS("Superuser created successfully: admin / admin1234"))
        else:
            self.stdout.write(self.style.WARNING("Superuser 'admin' already exists."))
