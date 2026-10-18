/**
 * TaskFlow — Collaborative Project Management Tool
 * Client-side interactions: Kanban Drag & Drop, Fallback Selects, Dynamic Notifications, Dialogs
 */

document.addEventListener('DOMContentLoaded', () => {
  initCSRF();
  initSidebar();
  initKanbanBoard();
  initNotificationPolling();
  initAlertDismissal();
});

// Get CSRF Token from cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

let csrfToken = null;
function initCSRF() {
  csrfToken = getCookie('csrftoken');
  // Fallback to meta tag or input
  if (!csrfToken) {
    const metaCsrf = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (metaCsrf) {
      csrfToken = metaCsrf.value;
    }
  }
}

// Mobile Sidebar Toggle
function initSidebar() {
  const toggleBtn = document.querySelector('.menu-toggle');
  const sidebar = document.querySelector('.sidebar');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('open');
      }
    });
  }
}

// Kanban Drag-and-Drop & Quick Select
function initKanbanBoard() {
  const cards = document.querySelectorAll('.task-card');
  const columnBodies = document.querySelectorAll('.column-body');

  if (cards.length === 0 && columnBodies.length === 0) return;

  cards.forEach(card => {
    card.setAttribute('draggable', 'true');

    card.addEventListener('dragstart', (e) => {
      const taskId = card.getAttribute('data-task-id');
      const currentStatus = card.getAttribute('data-status');
      e.dataTransfer.setData('text/plain', taskId);
      e.dataTransfer.setData('task-status', currentStatus);
      e.dataTransfer.effectAllowed = 'move';
      card.classList.add('dragging');
    });

    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      columnBodies.forEach(col => col.classList.remove('drag-over'));
    });

    // Handle Quick Status Dropdown (Accessible Fallback)
    const select = card.querySelector('.card-quick-status');
    if (select) {
      select.addEventListener('change', async (e) => {
        const taskId = card.getAttribute('data-task-id');
        const newStatus = e.target.value;
        await moveTask(card, taskId, newStatus);
      });
    }
  });

  columnBodies.forEach(colBody => {
    colBody.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      colBody.classList.add('drag-over');
    });

    colBody.addEventListener('dragleave', (e) => {
      if (!colBody.contains(e.relatedTarget)) {
        colBody.classList.remove('drag-over');
      }
    });

    colBody.addEventListener('drop', async (e) => {
      e.preventDefault();
      colBody.classList.remove('drag-over');

      const taskId = e.dataTransfer.getData('text/plain');
      const targetColumn = colBody.closest('.kanban-column');
      const newStatus = targetColumn.getAttribute('data-status');

      const card = document.querySelector(`.task-card[data-task-id="${taskId}"]`);
      if (card) {
        const currentStatus = card.getAttribute('data-status');
        if (currentStatus !== newStatus) {
          await moveTask(card, taskId, newStatus, colBody);
        }
      }
    });
  });
}

// Function to move task via AJAX and update UI
async function moveTask(card, taskId, newStatus, targetColumnBody = null) {
  const oldStatus = card.getAttribute('data-status');
  if (oldStatus === newStatus) return;

  // Find target column body if not provided
  if (!targetColumnBody) {
    const targetCol = document.querySelector(`.kanban-column[data-status="${newStatus}"]`);
    if (targetCol) {
      targetColumnBody = targetCol.querySelector('.column-body');
    }
  }

  // Optimistically move card in DOM
  const originalParent = card.parentElement;
  if (targetColumnBody) {
    targetColumnBody.appendChild(card);
    card.setAttribute('data-status', newStatus);

    // Update the quick-status select inside the card
    const select = card.querySelector('.card-quick-status');
    if (select) {
      select.value = newStatus;
    }

    updateColumnCounters();
  }

  try {
    const response = await fetch(`/tasks/${taskId}/move/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken || getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest'
      },
      body: JSON.stringify({ status: newStatus })
    });

    if (!response.ok) {
      throw new Error(`Server responded with ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || 'Failed to update task status');
    }

    // Update progress bar on page if present
    const progressFill = document.querySelector('.project-progress-fill');
    const progressText = document.querySelector('.project-progress-text');
    if (data.project_progress !== undefined && progressFill && progressText) {
      progressFill.style.width = `${data.project_progress}%`;
      progressText.textContent = `${data.project_progress}%`;
    }

  } catch (err) {
    console.error('Failed to move task:', err);
    // Revert optimistic move
    if (originalParent) {
      originalParent.appendChild(card);
      card.setAttribute('data-status', oldStatus);
      const select = card.querySelector('.card-quick-status');
      if (select) select.value = oldStatus;
      updateColumnCounters();
    }
    alert('Unable to move task. Please check your network connection or permissions.');
  }
}

// Recalculate badge counters for Kanban columns
function updateColumnCounters() {
  document.querySelectorAll('.kanban-column').forEach(col => {
    const countBadge = col.querySelector('.column-count');
    const cards = col.querySelectorAll('.task-card');
    if (countBadge) {
      countBadge.textContent = cards.length;
    }
  });
}

// Dynamic Notification Polling
function initNotificationPolling() {
  const badge = document.querySelector('.nav-badge');
  const bellBadge = document.querySelector('.icon-badge');

  // Poll every 20 seconds for active logged-in sessions
  if (badge || bellBadge) {
    setInterval(async () => {
      try {
        const response = await fetch('/api/notifications/count/');
        if (response.ok) {
          const data = await response.json();
          const count = data.unread_count;

          if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-block' : 'none';
          }
          if (bellBadge) {
            bellBadge.textContent = count;
            bellBadge.style.display = count > 0 ? 'flex' : 'none';
          }
        }
      } catch (e) {
        // Silent catch for background polling
      }
    }, 20000);
  }
}

// Alert dismissal
function initAlertDismissal() {
  document.querySelectorAll('.alert-close').forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-6px)';
        alert.style.transition = 'all 0.2s ease';
        setTimeout(() => alert.remove(), 200);
      }
    });
  });
}

// Modal helper functions
window.openModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal && typeof modal.showModal === 'function') {
    modal.showModal();
  }
};

window.closeModal = function(modalId) {
  const modal = document.getElementById(modalId);
  if (modal && typeof modal.close === 'function') {
    modal.close();
  }
};
