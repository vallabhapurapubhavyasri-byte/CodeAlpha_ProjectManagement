# TaskFlow — Collaborative Project Management Tool
**CodeAlpha Full Stack Development Internship — Task 3**

[![Django](https://img.shields.io/badge/Django-6.1-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.14%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/Tests-27%20Passed-brightgreen.svg)]()

TaskFlow is a full-stack, collaborative project management web application inspired by Trello and Asana. Designed with an original, distraction-free interface, it empowers software engineering teams and student project groups to create group workspaces, manage Kanban boards, assign tasks with role-based permissions, communicate within task discussion threads, and receive database-backed notifications.

---

## 🌟 Key Features

### 1. User Authentication & Profile Customization
- Secure user registration with email and username validation, password matching, and encrypted storage.
- Custom user profiles with job titles, biographies, and dynamically generated colored avatar badges.
- Session-based login/logout protected by Django’s security middleware.

### 2. Group Projects & Team Access Control
- Create, view, edit, and delete collaborative project workspaces.
- Role-based membership system:
  - **Project Owner:** Full authority to delete projects, manage team members, and moderate content.
  - **Project Admin:** Edit project settings, manage tasks, and invite/remove members.
  - **Team Member:** Create, assign, comment, and move tasks across Kanban columns.
  - **Viewer:** Read-only access to boards and task conversations.
- Strict backend authorization prevents unauthorized users from accessing private projects by guessing URLs or IDs.

### 3. Interactive Kanban Board
- 3 visual workflow stages: **To Do**, **In Progress**, and **Completed**.
- **Dual Control Architecture:**
  - **HTML5 Drag-and-Drop:** Intuitive drag-and-drop between columns with smooth visual feedback, dropzone indicators, and asynchronous REST API status updates.
  - **Accessible Select Dropdown:** Integrated on every card for mobile touchscreen devices and keyboard-driven accessibility.
- Live progress bar reflecting real-time project completion rate.
- Quick filter bar: Instant filtering by assignee, priority, or search keywords.

### 4. Task Management & Assignment
- Detailed task metadata: title, description, project, assignee, priority (Low, Medium, High, Urgent), status, and due dates.
- Strict assignee validation ensuring tasks can only be assigned to valid members of that specific project.
- Visual overdue indicators (red warning pills) and upcoming deadline badges.
- Dedicated **"My Tasks"** dashboard consolidating assignments across all projects.

### 5. Task Discussions & Collaboration
- Chronological comment stream on every task.
- Clean text rendering with automatic Django template escaping to prevent XSS.
- Author timestamps, author badges, and comment deletion permissions for authors and project managers.

### 6. Database-Backed Notifications (Bonus Feature)
- Event-driven notifications generated on:
  - Project invitations / additions
  - Task assignments and reassignments
  - New comments and discussion replies
  - Task status transitions
- Dynamic navbar notification bell with unread badge counter.
- Background polling every 20 seconds for seamless notification updates without page reloads.
- Dedicated Notifications Center with unread filtering, individual mark-read links, and "Mark All as Read".

### 7. Global Search & Workspace Discovery
- Search across all projects and tasks you have access to.
- Strictly respects permissions: Inaccessible projects and tasks are never revealed in search results.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Django, Django ORM, Django Auth, Django Messages |
| **Frontend** | HTML5, CSS3 (Modern custom variables, Flexbox, Grid), JavaScript (ES6 Fetch, HTML5 Drag & Drop) |
| **Templates** | Django Template Engine with custom template filters |
| **Database** | SQLite (development), PostgreSQL-ready for production |
| **Static Serving** | WhiteNoise |
| **Testing** | Django Automated Test Framework (TestCase, Client) |

---

## 📁 Project Structure

```text
CodeAlpha_ProjectManagement/
├── manage.py                          # Django management script
├── requirements.txt                   # Production & dev dependencies
├── README.md                          # Comprehensive documentation
├── .gitignore                         # Git exclusion rules
├── .env.example                       # Environment variables template
├── config/
│   ├── __init__.py
│   ├── settings.py                    # Project settings & WhiteNoise configuration
│   ├── urls.py                        # Root URL routing & static handlers
│   ├── wsgi.py                        # WSGI server entrypoint
│   └── asgi.py                        # ASGI server entrypoint
├── projects/
│   ├── __init__.py
│   ├── admin.py                       # Django Admin configuration & inlines
│   ├── apps.py                        # App configuration & signal registration
│   ├── forms.py                       # Forms for auth, projects, tasks, comments
│   ├── models.py                      # Project, Member, Task, Comment, Notification, Profile
│   ├── notifications.py               # Notification helper service
│   ├── signals.py                     # Automatic UserProfile creation
│   ├── urls.py                        # Application routes
│   ├── views.py                       # Full-stack view controllers & REST endpoints
│   ├── tests.py                       # 27 comprehensive automated tests
│   ├── templatetags/
│   │   ├── __init__.py
│   │   └── project_tags.py            # Custom template tags for project roles
│   ├── management/
│   │   └── commands/
│   │       ├── seed_data.py           # Realistic sample data seeder
│   │       └── create_demo_admin.py   # One-click demo admin generator
│   └── migrations/                    # Database migrations
├── static/
│   ├── css/
│   │   └── styles.css                 # Modern CSS styles & responsive layout
│   └── js/
│       └── app.js                     # Kanban drag & drop, AJAX handlers, polling
└── templates/
    ├── base.html                      # Main layout with sidebar & topbar
    ├── 404.html                       # Custom 404 error page
    └── projects/
        ├── landing.html               # Public showcase landing page
        ├── register.html              # Registration page
        ├── login.html                 # Login page
        ├── dashboard.html             # Main metrics dashboard
        ├── project_list.html          # Project gallery with filters
        ├── project_form.html          # Create/Edit project form
        ├── project_detail.html        # Project overview & settings
        ├── project_confirm_delete.html# Delete confirmation
        ├── project_members.html       # Member invitations & roles
        ├── project_board.html         # Visual Kanban board
        ├── task_form.html             # Create/Edit task form
        ├── task_detail.html           # Task discussion & metadata
        ├── task_confirm_delete.html   # Task delete confirmation
        ├── my_tasks.html              # Personal task overview
        ├── notifications.html         # Notification center
        ├── search.html                # Global search results
        ├── profile.html               # Account settings
        └── includes/
            └── task_card.html         # Reusable task card component
```

---

## 🚀 Getting Started Locally

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git

### 1. Clone or Open the Repository
```bash
git clone https://github.com/YOUR_USERNAME/CodeAlpha_ProjectManagement.git
cd CodeAlpha_ProjectManagement
```

### 2. Set Up a Virtual Environment (Recommended)
On Windows:
```powershell
python -m venv venv
venv\Scripts\activate
```
On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations
```bash
python manage.py migrate
```

### 5. Seed Demonstration Data (Optional but Recommended)
Populate the database with realistic demo teams, projects, Kanban cards, discussions, and notifications:
```bash
python manage.py seed_data
```
*Creates 4 demo accounts:*
- `alex_pm` (password: `demo1234`) — Lead Product Manager
- `sarah_dev` (password: `demo1234`) — Full-Stack Engineer
- `david_designer` (password: `demo1234`) — UI/UX Designer
- `maya_qa` (password: `demo1234`) — QA Specialist

### 6. Create an Administrator Superuser
To create a demo administrator (`admin` / `admin1234`):
```bash
python manage.py create_demo_admin
```
Or create a custom administrator:
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser!

---

## 🧪 Running Automated Tests

TaskFlow includes a comprehensive automated test suite with **27 tests** validating authentication, authorization, permissions, Kanban updates, comments, notifications, search, and dashboard metrics:

```bash
python manage.py test
```

### Expected Test Output:
```text
Creating test database for alias 'default'...
...........................
----------------------------------------------------------------------
Ran 27 tests in 138.006s

OK
Destroying test database for alias 'default'...
```

---

## 🌐 Bonus Feature: Real-Time WebSockets Upgrade Path

TaskFlow includes a robust database-backed notification system with client-side polling and instant AJAX status updates.

To upgrade to full real-time WebSockets via Django Channels:
1. Install Django Channels and Redis channel layer:
   ```bash
   pip install channels channels_redis daphne
   ```
2. In `config/settings.py`, add `'daphne'` to top of `INSTALLED_APPS` and define `ASGI_APPLICATION = 'config.asgi.application'`.
3. Configure `CHANNEL_LAYERS` with Redis backend:
   ```python
   CHANNEL_LAYERS = {
       "default": {
           "BACKEND": "channels_redis.core.RedisChannelLayer",
           "CONFIG": {"hosts": [("127.0.0.1", 6379)]},
       },
   }
   ```
4. Define consumers in `projects/consumers.py` and websocket URL routing in `projects/routing.py`.

---

## 🚢 Production Deployment Guide

TaskFlow is production-ready and configured with `whitenoise` for static files.

### Recommended Platform: Render / Railway / PythonAnywhere

1. **Environment Variables**:
   - `DJANGO_SECRET_KEY`: Set to a strong random key.
   - `DJANGO_DEBUG`: Set to `False`.
   - `ALLOWED_HOSTS`: `your-app-name.onrender.com,yourdomain.com`.

2. **Build Command**:
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```

3. **Start Command**:
   ```bash
   gunicorn config.wsgi:application
   ```

---

## 📦 GitHub Upload Instructions

To publish your project to a new repository on GitHub:

```bash
cd C:\Users\valla\.gemini\antigravity\scratch\CodeAlpha_ProjectManagement

# Initialize Git
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: CodeAlpha Task 3 - TaskFlow Project Management Tool"

# Rename branch to main
git branch -M main

# Add your GitHub remote repository
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/CodeAlpha_ProjectManagement.git

# Push to GitHub
git push -u origin main
```

---

## 📄 License & Credits
Developed by **Valla** as part of the **CodeAlpha Full Stack Development Internship** (Task 3: Collaborative Project Management Tool).
Released under the MIT License.
