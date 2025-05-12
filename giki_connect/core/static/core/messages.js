// messages.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const conversationItems = document.querySelectorAll('.conversation-item');
    const conversationView = document.getElementById('conversation-view');
    const noConversationMsg = document.getElementById('no-conversation-selected');
    const messagesList = document.getElementById('messages-list');
    const messageForm = document.getElementById('message-form');
    const receiverName = document.getElementById('receiver-name');
    const receiverInitial = document.getElementById('receiver-initial');
    const receiverIdInput = document.getElementById('receiver-id');
    const newMessageBtn = document.getElementById('new-message-btn');
    const newMessageModal = document.getElementById('new-message-modal');
    const closeModal = document.querySelector('.close-modal');
    const newMessageForm = document.getElementById('new-message-form');
    const receiverSearch = document.getElementById('receiver-search');
    const searchResults = document.getElementById('user-search-results');

    // Get CSRF token for POST requests
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Click event for conversation items
    conversationItems.forEach(item => {
        item.addEventListener('click', function() {
            // Remove active class from all items
            conversationItems.forEach(i => i.classList.remove('active'));
            
            // Add active class to clicked item
            this.classList.add('active');
            
            // Show conversation view and hide empty state
            noConversationMsg.classList.add('hidden');
            conversationView.classList.remove('hidden');
            
            // Get user ID and update receiver fields
            const userId = this.dataset.userId;
            const name = this.querySelector('.conversation-info h3').textContent;
            receiverName.textContent = name;
            receiverInitial.textContent = name.charAt(0);
            receiverIdInput.value = userId;
            
            // Load messages for this conversation
            loadMessages(userId);

            // Mark conversation as read
            if (this.classList.contains('unread')) {
                this.classList.remove('unread');
                const badge = this.querySelector('.unread-badge');
                if (badge) badge.remove();
            }
        });
    });

    // Load messages for a conversation
    function loadMessages(userId) {
        messagesList.innerHTML = '<div class="loading">Loading messages...</div>';
        
        fetch(`/api/messages/received/${userId}/`)
            .then(response => response.json())
            .then(data => {
                messagesList.innerHTML = '';
                
                if (data.length === 0) {
                    messagesList.innerHTML = '<div class="empty-state">No messages yet. Start the conversation!</div>';
                    return;
                }
                
                // Sort messages by timestamp
                data.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                
                // Display messages
                data.forEach(message => {
                    const isOutgoing = message.sender.user_id === currentUserId;
                    const messageElement = document.createElement('div');
                    messageElement.classList.add('message-bubble');
                    messageElement.classList.add(isOutgoing ? 'message-outgoing' : 'message-incoming');
                    
                    messageElement.innerHTML = `
                        <div class="message-content">${message.content}</div>
                        <div class="message-time">${formatTimestamp(message.timestamp)}</div>
                    `;
                    
                    messagesList.appendChild(messageElement);
                });
                
                // Scroll to bottom
                messagesList.scrollTop = messagesList.scrollHeight;
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                messagesList.innerHTML = '<div class="error">Failed to load messages. Please try again.</div>';
            });
    }

    // Format timestamp
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Send message
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const content = document.getElementById('message-content').value.trim();
        const receiverId = receiverIdInput.value;
        
        if (!content || !receiverId) return;
        
        const formData = new FormData();
        formData.append('content', content);
        formData.append('receiver_id', receiverId);
        
        fetch(`/api/messages/send/${currentUserId}/${receiverId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Clear input
            document.getElementById('message-content').value = '';
            
            // Add the new message to the message list
            const messageElement = document.createElement('div');
            messageElement.classList.add('message-bubble', 'message-outgoing');
            
            messageElement.innerHTML = `
                <div class="message-content">${data.content}</div>
                <div class="message-time">${formatTimestamp(data.timestamp)}</div>
            `;
            
            messagesList.appendChild(messageElement);
            
            // Scroll to bottom
            messagesList.scrollTop = messagesList.scrollHeight;
        })
        .catch(error => {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        });
    });

    // Modal functionality
    newMessageBtn.addEventListener('click', function() {
        newMessageModal.style.display = 'block';
    });
    
    closeModal.addEventListener('click', function() {
        newMessageModal.style.display = 'none';
    });
    
    window.addEventListener('click', function(e) {
        if (e.target === newMessageModal) {
            newMessageModal.style.display = 'none';
        }
    });

    // User search functionality
    let searchTimeout;
    receiverSearch.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        
        const query = this.value.trim();
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetch(`/api/users/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    searchResults.innerHTML = '';
                    
                    if (data.length === 0) {
                        searchResults.innerHTML = '<div class="search-result-item">No users found</div>';
                    } else {
                        data.forEach(user => {
                            const item = document.createElement('div');
                            item.classList.add('search-result-item');
                            item.textContent = user.name;
                            item.dataset.userId = user.user_id;
                            
                            item.addEventListener('click', function() {
                                receiverSearch.value = user.name;
                                document.getElementById('new-message-form').dataset.receiverId = user.user_id;
                                searchResults.style.display = 'none';
                            });
                            
                            searchResults.appendChild(item);
                        });
                    }
                    
                    searchResults.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error searching users:', error);
                });
        }, 300);
    });

    // Send new message
    newMessageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const receiverId = this.dataset.receiverId;
        const content = document.getElementById('new-message-content').value.trim();
        
        if (!receiverId || !content) {
            alert('Please select a recipient and enter a message.');
            return;
        }
        
        const formData = new FormData();
        formData.append('content', content);
        formData.append('receiver_id', receiverId);
        
        fetch(`/api/messages/send/${currentUserId}/${receiverId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
            },
            body: formData
        })
        .then(response => response.json())
        .then(() => {
            // Reset and close modal
            newMessageForm.reset();
            newMessageModal.style.display = 'none';
            
            // Reload page to show new conversation
            window.location.reload();
        })
        .catch(error => {
            console.error('Error sending message:', error);
            alert('Failed to send message. Please try again.');
        });
    });

    // Replace with dynamic user ID from your authentication context
    const currentUserId = document.body.dataset.userId || '1';
});