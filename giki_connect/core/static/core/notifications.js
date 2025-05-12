// notifications.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const markAllReadBtn = document.getElementById('mark-all-read');
    const filterDropdown = document.querySelectorAll('.dropdown-item[data-filter]');
    const notificationItems = document.querySelectorAll('.notification-item');
    const markReadBtns = document.querySelectorAll('.mark-read-btn');
    const acceptRequestBtns = document.querySelectorAll('.accept-request-btn');
    const declineRequestBtns = document.querySelectorAll('.decline-request-btn');

    // Get CSRF token for POST requests
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Mark a single notification as read
    function markAsRead(notificationId) {
        fetch(`/notifications/read/${notificationId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Find the notification item and update its appearance
            const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (notificationItem) {
                notificationItem.classList.remove('unread');
                
                // Remove the unread indicator
                const unreadIndicator = notificationItem.querySelector('.unread-indicator');
                if (unreadIndicator) {
                    unreadIndicator.remove();
                }
                
                // Remove the mark as read button
                const markReadBtn = notificationItem.querySelector('.mark-read-btn');
                if (markReadBtn) {
                    markReadBtn.remove();
                }
            }
            
            // Update the notification counter in navbar if exists
            updateNotificationCounter();
        })
        .catch(error => {
            console.error('Error marking notification as read:', error);
        });
    }

    // Mark all notifications as read
    function markAllAsRead() {
        fetch('/notifications/read-all/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update all notification items
            notificationItems.forEach(item => {
                item.classList.remove('unread');
                
                // Remove unread indicators
                const unreadIndicator = item.querySelector('.unread-indicator');
                if (unreadIndicator) {
                    unreadIndicator.remove();
                }
                
                // Remove mark as read buttons
                const markReadBtn = item.querySelector('.mark-read-btn');
                if (markReadBtn) {
                    markReadBtn.remove();
                }
            });
            
            // Update the notification counter in navbar
            updateNotificationCounter(0);
        })
        .catch(error => {
            console.error('Error marking all notifications as read:', error);
        });
    }

    // Update notification counter in navbar
    function updateNotificationCounter(count) {
        const counter = document.querySelector('.notification-counter');
        if (counter) {
            if (count !== undefined) {
                // If count is provided, set it directly
                if (count === 0) {
                    counter.style.display = 'none';
                } else {
                    counter.textContent = count;
                    counter.style.display = 'inline-block';
                }
            } else {
                // Otherwise, count unread notifications
                const unreadCount = document.querySelectorAll('.notification-item.unread').length;
                if (unreadCount === 0) {
                    counter.style.display = 'none';
                } else {
                    counter.textContent = unreadCount;
                    counter.style.display = 'inline-block';
                }
            }
        }
    }

    // Handle connection request actions
    function handleConnectionRequest(notificationId, action) {
        fetch(`/api/connections/manage/${notificationId}/${action}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Find the notification item and update its appearance
            const notificationItem = document.querySelector(`.notification-item[data-id="${notificationId}"]`);
            if (notificationItem) {
                // Replace connection buttons with a status message
                const connectionButtons = notificationItem.querySelector('.connection-buttons');
                if (connectionButtons) {
                    const statusMessage = document.createElement('span');
                    statusMessage.className = action === 'accept' ? 'text-success' : 'text-danger';
                    statusMessage.textContent = action === 'accept' ? 'Request accepted' : 'Request declined';
                    connectionButtons.replaceWith(statusMessage);
                }
                
                // Mark as read
                markAsRead(notificationId);
            }
        })
        .catch(error => {
            console.error(`Error ${action}ing connection request:`, error);
        });
    }

    // Filter notifications
    function filterNotifications(filterType) {
        notificationItems.forEach(item => {
            if (filterType === 'all') {
                item.style.display = 'flex';
            } else if (filterType === 'unread') {
                item.style.display = item.classList.contains('unread') ? 'flex' : 'none';
            } else {
                // Filter by notification type
                item.style.display = item.dataset.type === filterType ? 'flex' : 'none';
            }
        });
        
        // Show empty state if no visible notifications
        const visibleNotifications = Array.from(notificationItems).filter(item => 
            item.style.display === 'flex' || item.style.display === ''
        );
        
        let emptyState = document.querySelector('.empty-notifications');
        
        if (visibleNotifications.length === 0) {
            if (!emptyState) {
                emptyState = document.createElement('div');
                emptyState.className = 'empty-notifications';
                emptyState.innerHTML = `
                    <div class="empty-icon">
                        <i class="far fa-bell-slash"></i>
                    </div>
                    <h3>No notifications found</h3>
                    <p>No ${filterType === 'all' ? '' : filterType.toLowerCase()} notifications available.</p>
                `;
                
                const notificationsList = document.querySelector('.notifications-list');
                notificationsList.appendChild(emptyState);
            }
        } else if (emptyState) {
            emptyState.remove();
        }
    }

    // Event Listeners
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function() {
            markAllAsRead();
        });
    }

    filterDropdown.forEach(item => {
        item.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Update active state
            filterDropdown.forEach(i => i.classList.remove('active'));
            this.classList.add('active');
            
            // Apply filter
            filterNotifications(this.dataset.filter);
        });
    });

    markReadBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const notificationId = this.dataset.id;
            markAsRead(notificationId);
        });
    });

    acceptRequestBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const notificationItem = this.closest('.notification-item');
            const notificationId = notificationItem.dataset.id;
            handleConnectionRequest(notificationId, 'accept');
        });
    });

    declineRequestBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const notificationItem = this.closest('.notification-item');
            const notificationId = notificationItem.dataset.id;
            handleConnectionRequest(notificationId, 'decline');
        });
    });

    // Click event for notification items
    notificationItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't handle clicks on buttons
            if (
                e.target.classList.contains('mark-read-btn') || 
                e.target.classList.contains('accept-request-btn') || 
                e.target.classList.contains('decline-request-btn')
            ) {
                return;
            }
            
            // If unread, mark as read
            if (this.classList.contains('unread')) {
                const notificationId = this.dataset.id;
                markAsRead(notificationId);
            }
            
            // Handle different notification types
            const type = this.dataset.type;
            const content = this.querySelector('.notification-text').textContent;
            
            // Redirect based on notification type
            if (type === 'Message' && content.includes('sent you a message')) {
                // Extract user id if possible
                const match = content.match(/User (\d+) sent you a message/);
                if (match && match[1]) {
                    window.location.href = `/messages/?user=${match[1]}`;
                } else {
                    window.location.href = '/messages/';
                }
            } else if (type === 'Connection' && content.includes('connection request')) {
                window.location.href = '/connections/requests/';
            } else if (type === 'Event') {
                // Try to extract event ID
                const match = content.match(/Event (\d+)/);
                if (match && match[1]) {
                    window.location.href = `/events/${match[1]}/`;
                } else {
                    window.location.href = '/events/';
                }
            }
            // Other types may not have specific redirects
        });
    });
});