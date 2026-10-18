from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json
from .models import Project, ProjectMember, Task, TaskComment, Notification, UserProfile
from .notifications import create_notification


class BaseTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create users
        self.user1 = User.objects.create_user(
            username='user1', email='user1@example.com', password='password123',
            first_name='Alice', last_name='Smith'
        )
        self.user2 = User.objects.create_user(
            username='user2', email='user2@example.com', password='password123',
            first_name='Bob', last_name='Jones'
        )
        self.user3 = User.objects.create_user(
            username='user3', email='user3@example.com', password='password123',
            first_name='Charlie', last_name='Brown'
        )

        # Create a sample project owned by user1
        self.project1 = Project.objects.create(
            title="Alpha Project",
            description="Alpha Project Description",
            owner=self.user1,
            status="active"
        )
        # Add user2 as member
        self.member_user2 = ProjectMember.objects.create(
            project=self.project1,
            user=self.user2,
            role="member"
        )


class AuthenticationTests(BaseTestCase):
    def test_registration_success(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'Person',
            'email': 'new@example.com',
            'job_title': 'Developer',
            'password': 'safePassword123',
            'password_confirm': 'safePassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        new_user = User.objects.get(username='newuser')
        self.assertEqual(new_user.profile.job_title, 'Developer')

    def test_registration_password_mismatch(self):
        response = self.client.post(reverse('register'), {
            'username': 'baduser',
            'first_name': 'Bad',
            'last_name': 'Match',
            'email': 'bad@example.com',
            'password': 'passwordOne',
            'password_confirm': 'passwordTwo'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())
        self.assertContains(response, "Passwords do not match.")

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'user1',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'user1',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_logout(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('landing'))

    def test_unauthorized_dashboard_access_redirects(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)


class ProjectTests(BaseTestCase):
    def test_project_creation(self):
        self.client.login(username='user1', password='password123')
        response = self.client.post(reverse('project_create'), {
            'title': 'New Web App',
            'description': 'Building next-gen dashboard',
            'status': 'planning'
        })
        self.assertEqual(response.status_code, 302)
        project = Project.objects.filter(title='New Web App').first()
        self.assertIsNotNone(project)
        self.assertEqual(project.owner, self.user1)

    def test_project_editing_by_owner(self):
        self.client.login(username='user1', password='password123')
        response = self.client.post(reverse('project_edit', args=[self.project1.id]), {
            'title': 'Alpha Project Updated',
            'description': 'Updated scope',
            'status': 'completed'
        })
        self.assertEqual(response.status_code, 302)
        self.project1.refresh_from_db()
        self.assertEqual(self.project1.title, 'Alpha Project Updated')
        self.assertEqual(self.project1.status, 'completed')

    def test_unauthorized_project_access_denied(self):
        # user3 has no membership in project1
        self.client.login(username='user3', password='password123')
        response = self.client.get(reverse('project_detail', args=[self.project1.id]))
        # Should redirect to project_list with error message
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('project_list'))

    def test_project_deletion_by_owner(self):
        self.client.login(username='user1', password='password123')
        response = self.client.post(reverse('project_delete', args=[self.project1.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Project.objects.filter(id=self.project1.id).exists())

    def test_prevent_non_owner_project_deletion(self):
        self.client.login(username='user2', password='password123')
        response = self.client.post(reverse('project_delete', args=[self.project1.id]))
        self.assertEqual(response.status_code, 302)
        # Project should still exist!
        self.assertTrue(Project.objects.filter(id=self.project1.id).exists())

    def test_add_and_remove_member(self):
        self.client.login(username='user1', password='password123')
        # Add user3
        response = self.client.post(reverse('project_members', args=[self.project1.id]), {
            'user': self.user3.id,
            'role': 'member'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.project1.is_member(self.user3))
        # Notification created for user3
        self.assertTrue(Notification.objects.filter(recipient=self.user3).exists())

        # Now remove user3
        membership = ProjectMember.objects.get(project=self.project1, user=self.user3)
        response = self.client.post(reverse('project_member_remove', args=[self.project1.id, membership.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.project1.is_member(self.user3))

    def test_prevent_duplicate_membership(self):
        # user2 is already a member
        with self.assertRaises(Exception):
            ProjectMember.objects.create(
                project=self.project1,
                user=self.user2,
                role='member'
            )


class TaskTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.task1 = Task.objects.create(
            title="Setup database schema",
            description="Create tables and relations",
            project=self.project1,
            creator=self.user1,
            assignee=self.user2,
            status="todo",
            priority="high",
            due_date=timezone.now().date() + timedelta(days=3)
        )

    def test_task_creation_in_project(self):
        self.client.login(username='user1', password='password123')
        response = self.client.post(reverse('task_create', args=[self.project1.id]), {
            'title': 'Write unit tests',
            'description': 'Complete test coverage',
            'assignee': self.user2.id,
            'status': 'todo',
            'priority': 'urgent',
            'due_date': (timezone.now().date() + timedelta(days=2)).isoformat()
        })
        self.assertEqual(response.status_code, 302)
        new_task = Task.objects.filter(title='Write unit tests').first()
        self.assertIsNotNone(new_task)
        self.assertEqual(new_task.assignee, self.user2)
        # Notification for user2
        self.assertTrue(Notification.objects.filter(recipient=self.user2, task=new_task).exists())

    def test_prevent_assigning_task_to_non_member(self):
        self.client.login(username='user1', password='password123')
        # user3 is not in project1
        response = self.client.post(reverse('task_create', args=[self.project1.id]), {
            'title': 'Invalid task assignment',
            'description': 'Assigning to user3',
            'assignee': self.user3.id,
            'status': 'todo',
            'priority': 'medium'
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(title='Invalid task assignment').exists())

    def test_move_task_status_api(self):
        self.client.login(username='user1', password='password123')
        response = self.client.post(
            reverse('task_move_api', args=[self.task1.id]),
            data=json.dumps({'status': 'in_progress'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.status, 'in_progress')

    def test_unauthorized_task_modification_denied(self):
        self.client.login(username='user3', password='password123')
        # user3 cannot move task in project1
        response = self.client.post(
            reverse('task_move_api', args=[self.task1.id]),
            data=json.dumps({'status': 'completed'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 403)
        self.task1.refresh_from_db()
        self.assertNotEqual(self.task1.status, 'completed')


class CommentTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.task = Task.objects.create(
            title="Design landing page",
            project=self.project1,
            creator=self.user1,
            assignee=self.user2,
            status="todo",
            priority="medium"
        )

    def test_add_valid_comment(self):
        self.client.login(username='user2', password='password123')
        response = self.client.post(reverse('task_comment_add', args=[self.task.id]), {
            'content': 'I have created initial mockups for review.'
        })
        self.assertEqual(response.status_code, 302)
        comment = TaskComment.objects.filter(task=self.task, author=self.user2).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'I have created initial mockups for review.')
        # User1 (creator) gets notification
        self.assertTrue(Notification.objects.filter(recipient=self.user1, task=self.task).exists())

    def test_reject_empty_comment(self):
        self.client.login(username='user2', password='password123')
        response = self.client.post(reverse('task_comment_add', args=[self.task.id]), {
            'content': '   '
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(TaskComment.objects.filter(task=self.task).count(), 0)

    def test_delete_comment_by_author(self):
        comment = TaskComment.objects.create(task=self.task, author=self.user2, content="Test comment")
        self.client.login(username='user2', password='password123')
        response = self.client.post(reverse('task_comment_delete', args=[comment.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TaskComment.objects.filter(id=comment.id).exists())

    def test_delete_comment_by_non_author_forbidden(self):
        comment = TaskComment.objects.create(task=self.task, author=self.user2, content="Secret comment")
        self.client.login(username='user3', password='password123')
        response = self.client.post(reverse('task_comment_delete', args=[comment.id]))
        self.assertEqual(response.status_code, 302)
        # Comment should NOT be deleted
        self.assertTrue(TaskComment.objects.filter(id=comment.id).exists())


class NotificationTests(BaseTestCase):
    def test_notification_mark_read(self):
        notif = create_notification(
            recipient=self.user2,
            actor=self.user1,
            verb="assigned you to a task",
            project=self.project1
        )
        self.assertFalse(notif.is_read)

        self.client.login(username='user2', password='password123')
        response = self.client.get(reverse('notification_mark_read', args=[notif.id]))
        self.assertEqual(response.status_code, 302)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_prevent_access_other_user_notifications(self):
        notif = create_notification(
            recipient=self.user1,
            actor=self.user2,
            verb="assigned you to a task"
        )
        # user3 tries to mark user1's notification as read
        self.client.login(username='user3', password='password123')
        response = self.client.get(reverse('notification_mark_read', args=[notif.id]))
        self.assertEqual(response.status_code, 404)
        notif.refresh_from_db()
        self.assertFalse(notif.is_read)

    def test_mark_all_read(self):
        create_notification(recipient=self.user1, actor=self.user2, verb="update 1")
        create_notification(recipient=self.user1, actor=self.user2, verb="update 2")
        self.assertEqual(Notification.objects.filter(recipient=self.user1, is_read=False).count(), 2)

        self.client.login(username='user1', password='password123')
        response = self.client.post(reverse('notification_mark_all_read'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Notification.objects.filter(recipient=self.user1, is_read=False).count(), 0)


class DashboardAndSearchTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.task_todo = Task.objects.create(
            title="Todo Task", project=self.project1, creator=self.user1,
            assignee=self.user1, status="todo"
        )
        self.task_done = Task.objects.create(
            title="Done Task", project=self.project1, creator=self.user1,
            assignee=self.user1, status="completed"
        )

    def test_dashboard_metrics_calculation(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_projects'], 1)
        self.assertEqual(response.context['total_assigned_tasks'], 2)
        self.assertEqual(response.context['tasks_todo'], 1)
        self.assertEqual(response.context['tasks_completed'], 1)

    def test_search_accessible_projects_and_tasks(self):
        self.client.login(username='user1', password='password123')
        response = self.client.get(reverse('search') + '?q=Alpha')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alpha Project")

    def test_search_does_not_reveal_inaccessible_projects(self):
        # user3 has no access to project1
        self.client.login(username='user3', password='password123')
        response = self.client.get(reverse('search') + '?q=Alpha')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Alpha Project Description")
        self.assertEqual(len(response.context['matching_projects']), 0)
