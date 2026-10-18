from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from projects.models import Project, ProjectMember, Task, TaskComment, Notification, UserProfile
from projects.notifications import create_notification


class Command(BaseCommand):
    help = 'Seeds realistic sample data for TaskFlow demonstration'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting TaskFlow sample data seeding...'))

        # 1. Create Demo Users
        users_data = [
            {'username': 'alex_pm', 'email': 'alex@taskflow.demo', 'first_name': 'Alex', 'last_name': 'Morgan', 'title': 'Lead Product Manager'},
            {'username': 'sarah_dev', 'email': 'sarah@taskflow.demo', 'first_name': 'Sarah', 'last_name': 'Chen', 'title': 'Senior Full-Stack Engineer'},
            {'username': 'david_designer', 'email': 'david@taskflow.demo', 'first_name': 'David', 'last_name': 'Kim', 'title': 'UI/UX Product Designer'},
            {'username': 'maya_qa', 'email': 'maya@taskflow.demo', 'first_name': 'Maya', 'last_name': 'Patel', 'title': 'Quality Assurance Specialist'},
        ]

        created_users = {}
        for u in users_data:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    'email': u['email'],
                    'first_name': u['first_name'],
                    'last_name': u['last_name'],
                }
            )
            user.set_password('demo1234')
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.job_title = u['title']
            profile.bio = f"{u['title']} at CodeAlpha Tech. Passionate about building great software and collaborative team experiences."
            profile.save()

            created_users[u['username']] = user
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created demo user: {u['username']} (password: demo1234)"))
            else:
                self.stdout.write(f"Updated user: {u['username']}")

        alex = created_users['alex_pm']
        sarah = created_users['sarah_dev']
        david = created_users['david_designer']
        maya = created_users['maya_qa']

        today = timezone.now().date()

        # 2. Project 1: TaskFlow Core Web App
        p1, _ = Project.objects.get_or_create(
            title='TaskFlow Web Platform V1',
            defaults={
                'description': 'Main web application build featuring full Kanban board, real-time collaboration, notification center, and team permissions.',
                'owner': alex,
                'status': 'active'
            }
        )
        # Add members
        ProjectMember.objects.get_or_create(project=p1, user=sarah, defaults={'role': 'admin'})
        ProjectMember.objects.get_or_create(project=p1, user=david, defaults={'role': 'member'})
        ProjectMember.objects.get_or_create(project=p1, user=maya, defaults={'role': 'member'})

        # Tasks for Project 1
        tasks_p1 = [
            {
                'title': 'Design high-fidelity Kanban board mockups',
                'description': 'Create Figma wireframes and UI components for 3-column boards, task cards, modal dialogs, and drag-and-drop feedback states.',
                'assignee': david,
                'creator': alex,
                'status': 'completed',
                'priority': 'high',
                'due_date': today - timedelta(days=2),
                'comments': [
                    (alex, "Please ensure color contrast passes WCAG AA standards."),
                    (david, "Updated palette with deep slate headers and accessible indigo badges. Ready for review!")
                ]
            },
            {
                'title': 'Implement user authentication and session management',
                'description': 'Set up secure registration with email validation, login/logout, password confirm checks, and protected routes.',
                'assignee': sarah,
                'creator': alex,
                'status': 'completed',
                'priority': 'urgent',
                'due_date': today - timedelta(days=1),
                'comments': [
                    (sarah, "All authentication flows tested and integrated with Django messages framework.")
                ]
            },
            {
                'title': 'Build Drag-and-Drop Kanban interactions',
                'description': 'Add native HTML5 drag-and-drop support with asynchronous REST API updates and fallback dropdown selectors for mobile/touch users.',
                'assignee': sarah,
                'creator': alex,
                'status': 'in_progress',
                'priority': 'urgent',
                'due_date': today + timedelta(days=1),
                'comments': [
                    (sarah, "API endpoint handles JSON requests and CSRF tokens smoothly. Tuning dropzone highlights."),
                    (alex, "Great progress, make sure status changes trigger notifications for the assignee.")
                ]
            },
            {
                'title': 'Develop notification center & badge counter',
                'description': 'Database-backed notifications for project invites, task assignments, status changes, and discussion replies.',
                'assignee': sarah,
                'creator': alex,
                'status': 'in_progress',
                'priority': 'high',
                'due_date': today + timedelta(days=3),
                'comments': [
                    (alex, "Include 'Mark all as read' quick action.")
                ]
            },
            {
                'title': 'Cross-browser manual testing and bug triage',
                'description': 'Execute test matrix across Chrome, Firefox, Edge, and mobile Safari. Verify form validations and edge cases.',
                'assignee': maya,
                'creator': alex,
                'status': 'todo',
                'priority': 'medium',
                'due_date': today + timedelta(days=5),
                'comments': [
                    (maya, "Test plan ready. Will begin validation as soon as drag-and-drop is merged.")
                ]
            },
            {
                'title': 'Prepare README documentation and demo walkthrough',
                'description': 'Document architecture, dependencies, setup instructions, database migrations, and deployment guide.',
                'assignee': alex,
                'creator': alex,
                'status': 'todo',
                'priority': 'medium',
                'due_date': today + timedelta(days=7),
                'comments': []
            }
        ]

        for t_info in tasks_p1:
            t, _ = Task.objects.get_or_create(
                project=p1,
                title=t_info['title'],
                defaults={
                    'description': t_info['description'],
                    'assignee': t_info['assignee'],
                    'creator': t_info['creator'],
                    'status': t_info['status'],
                    'priority': t_info['priority'],
                    'due_date': t_info['due_date'],
                }
            )
            for c_author, c_text in t_info['comments']:
                TaskComment.objects.get_or_create(
                    task=t,
                    author=c_author,
                    content=c_text
                )

        # 2. Project 2: Mobile Companion App
        p2, _ = Project.objects.get_or_create(
            title='Mobile Companion App Design',
            defaults={
                'description': 'Research and design responsive mobile interface for on-the-go task tracking and push notifications.',
                'owner': david,
                'status': 'planning'
            }
        )
        ProjectMember.objects.get_or_create(project=p2, user=alex, defaults={'role': 'member'})
        ProjectMember.objects.get_or_create(project=p2, user=sarah, defaults={'role': 'member'})

        Task.objects.get_or_create(
            project=p2,
            title='User research interviews with beta testers',
            defaults={
                'description': 'Interview 5 remote teams about mobile project tracking pain points and top 3 needed features.',
                'assignee': david,
                'creator': david,
                'status': 'in_progress',
                'priority': 'medium',
                'due_date': today + timedelta(days=4)
            }
        )
        Task.objects.get_or_create(
            project=p2,
            title='Define Mobile App Architecture & offline sync',
            defaults={
                'description': 'Evaluate local storage caching and background sync strategies for intermittent connectivity.',
                'assignee': sarah,
                'creator': david,
                'status': 'todo',
                'priority': 'high',
                'due_date': today + timedelta(days=10)
            }
        )

        # 3. Create Sample Notifications
        create_notification(
            recipient=alex,
            actor=sarah,
            verb=f"updated task 'Build Drag-and-Drop Kanban interactions' status to 'In Progress'",
            project=p1
        )
        create_notification(
            recipient=sarah,
            actor=alex,
            verb=f"assigned you to task 'Build Drag-and-Drop Kanban interactions' in project '{p1.title}'",
            project=p1
        )
        create_notification(
            recipient=david,
            actor=alex,
            verb=f"added you to project '{p1.title}' as Team Member",
            project=p1
        )
        create_notification(
            recipient=maya,
            actor=alex,
            verb=f"assigned you to task 'Cross-browser manual testing and bug triage' in project '{p1.title}'",
            project=p1
        )

        self.stdout.write(self.style.SUCCESS(
            "\nSuccessfully seeded TaskFlow with:\n"
            "- 4 demo users (alex_pm, sarah_dev, david_designer, maya_qa with password 'demo1234')\n"
            "- 2 projects with assigned teams and permissions\n"
            "- 8 tasks across To Do, In Progress, and Completed\n"
            "- Realistic task comments and conversations\n"
            "- Real database-backed notifications"
        ))
