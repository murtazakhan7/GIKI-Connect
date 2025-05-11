document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const eventModal = document.getElementById('event-modal');
    const closeModal = document.querySelector('.close-modal');
    const detailButtons = document.querySelectorAll('.btn-details');
    const rsvpButtons = document.querySelectorAll('.btn-rsvp');
    const changeRsvpButtons = document.querySelectorAll('.btn-change-rsvp');
    const rsvpForm = document.getElementById('rsvp-form');
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('event-search');
    const filterDate = document.getElementById('filter-date');
    const filterRsvp = document.getElementById('filter-rsvp');
    
    // Event listeners for filters
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            filterEvents();
        });
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                filterEvents();
            }
        });
    }
    
    if (filterDate) {
        filterDate.addEventListener('change', function() {
            filterEvents();
        });
    }
    
    if (filterRsvp) {
        filterRsvp.addEventListener('change', function() {
            filterEvents();
        });
    }
    
    // Open modal with event details
    detailButtons.forEach(button => {
        button.addEventListener('click', function() {
            const eventId = this.getAttribute('data-event-id');
            openEventModal(eventId);
        });
    });
    
    // Quick RSVP from the event card
    rsvpButtons.forEach(button => {
        button.addEventListener('click', function() {
            const eventId = this.getAttribute('data-event-id');
            const status = this.getAttribute('data-status');
            submitRsvp(eventId, status);
        });
    });
    
    // Change RSVP buttons
    changeRsvpButtons.forEach(button => {
        button.addEventListener('click', function() {
            const eventCard = this.closest('.event-card');
            const eventId = eventCard.getAttribute('data-event-id');
            openEventModal(eventId);
        });
    });
    
    // Close modal
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            eventModal.style.display = 'none';
            document.body.style.overflow = '';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === eventModal) {
            eventModal.style.display = 'none';
            document.body.style.overflow = '';
        }
    });
    
    // RSVP form submission
    if (rsvpForm) {
        rsvpForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const eventId = document.getElementById('modal-event-id').value;
            const rsvpStatus = document.querySelector('input[name="rsvp_status"]:checked').value;
            
            submitRsvp(eventId, rsvpStatus);
        });
    }
    
    // Function to open event modal and fetch details
    function openEventModal(eventId) {
        // In a real application, fetch event details via AJAX
        // For demonstration, we'll use data from the DOM
        
        // Find the event card with matching ID
        const eventCard = document.querySelector(`.event-card[data-event-id="${eventId}"]`);
        
        if (eventCard) {
            // Extract event details from the card
            const title = eventCard.querySelector('h3').textContent;
            const dateText = eventCard.querySelector('.event-date').textContent;
            const timeText = eventCard.querySelector('.event-time').textContent;
            const locationText = eventCard.querySelector('.event-location').textContent;
            const organizerText = eventCard.querySelector('.event-organizer').textContent;
            const capacityText = eventCard.querySelector('.event-capacity').textContent;
            const description = eventCard.querySelector('.event-description p').textContent;
            
            // Set modal content
            document.getElementById('modal-event-title').textContent = title;
            document.getElementById('modal-event-date').textContent = dateText;
            document.getElementById('modal-event-time').textContent = timeText.replace(/^\s*<i class="fa fa-clock-o"><\/i>\s*/, '');
            document.getElementById('modal-event-location').textContent = locationText.replace(/^\s*<i class="fa fa-map-marker"><\/i>\s*/, '');
            document.getElementById('modal-event-organizer').textContent = organizerText.replace(/^\s*<i class="fa fa-user"><\/i>\s*Organized by:\s*/, '');
            document.getElementById('modal-event-capacity').textContent = capacityText.replace(/^\s*<i class="fa fa-users"><\/i>\s*Capacity:\s*/, '');
            document.getElementById('modal-event-description').textContent = description;
            document.getElementById('modal-event-id').value = eventId;
            
            // Check if user has an existing RSVP
            const rsvpStatus = eventCard.querySelector('.rsvp-status');
            if (rsvpStatus) {
                const status = rsvpStatus.classList.contains('yes') ? 'Yes' : 
                               rsvpStatus.classList.contains('maybe') ? 'Maybe' : 'No';
                
                // Set the appropriate radio button
                document.querySelector(`input[name="rsvp_status"][value="${status}"]`).checked = true;
            } else {
                // No existing RSVP, set default to unchecked
                const radioInputs = document.querySelectorAll('input[name="rsvp_status"]');
                radioInputs.forEach(input => {
                    input.checked = false;
                });
            }
            
            // In a real application, you would also fetch attendees list via AJAX
            fetchAttendees(eventId);
            
            // Show modal
            eventModal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent scrolling behind modal
        }
    }
    
    // Function to submit RSVP
    function submitRsvp(eventId, status) {
        // Get CSRF token from the form
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        // Prepare data for submission
        const formData = new FormData();
        formData.append('event_id', eventId);
        formData.append('status', status);
        
        // Send AJAX request
        fetch('/events/rsvp/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update UI to reflect the new RSVP status
                updateRsvpUI(eventId, status);
                // Close modal if it's open
                if (eventModal.style.display === 'block') {
                    eventModal.style.display = 'none';
                    document.body.style.overflow = '';
                }
                // Show success message
                showNotification(data.message || 'RSVP updated successfully!', 'success');
            } else {
                // Show error message
                showNotification(data.message || 'Failed to update RSVP', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('An error occurred while updating your RSVP', 'error');
        });
    }
    
    // Function to update UI after RSVP
    function updateRsvpUI(eventId, status) {
        const eventCard = document.querySelector(`.event-card[data-event-id="${eventId}"]`);
        
        if (eventCard) {
            // Remove existing RSVP buttons or status
            const existingRsvpButtons = eventCard.querySelector('.rsvp-buttons');
            const existingRsvpStatus = eventCard.querySelector('.rsvp-status');
            
            if (existingRsvpButtons) {
                existingRsvpButtons.remove();
            }
            
            if (existingRsvpStatus) {
                existingRsvpStatus.remove();
            }
            
            // Create new RSVP status element
            const rsvpStatus = document.createElement('div');
            rsvpStatus.className = `rsvp-status ${status.toLowerCase()}`;
            rsvpStatus.innerHTML = `
                <span>Your RSVP: ${status}</span>
                <button class="btn-change-rsvp">Change</button>
            `;
            
            // Add event listener to the new change button
            const changeButton = rsvpStatus.querySelector('.btn-change-rsvp');
            changeButton.addEventListener('click', function() {
                openEventModal(eventId);
            });
            
            // Add the new status to the event card
            const actionsDiv = eventCard.querySelector('.event-actions');
            actionsDiv.appendChild(rsvpStatus);
            
            // Update attendees count if available
            updateAttendeesCount(eventId, status);
        }
    }
    
    // Function to update attendees count after RSVP
    function updateAttendeesCount(eventId, status) {
        const eventCard = document.querySelector(`.event-card[data-event-id="${eventId}"]`);
        
        if (eventCard && status === 'Yes') {
            let attendeesElem = eventCard.querySelector('.event-attendees');
            
            if (attendeesElem) {
                // Extract current count
                const countText = attendeesElem.textContent;
                const countMatch = countText.match(/(\d+)/);
                
                if (countMatch) {
                    const currentCount = parseInt(countMatch[1], 10);
                    // Update count
                    attendeesElem.innerHTML = `<i class="fa fa-check-circle"></i> ${currentCount + 1} people attending`;
                }
            } else {
                // Create new attendees element if it doesn't exist
                const detailsDiv = eventCard.querySelector('.event-details');
                attendeesElem = document.createElement('p');
                attendeesElem.className = 'event-attendees';
                attendeesElem.innerHTML = '<i class="fa fa-check-circle"></i> 1 people attending';
                detailsDiv.appendChild(attendeesElem);
            }
        }
    }
    
    // Function to fetch attendees for an event
    function fetchAttendees(eventId) {
        // Get CSRF token from the form
        const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
        
        // Send AJAX request
        fetch(`/events/${eventId}/attendees/`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Update attendees list in modal
            updateAttendeesUI(data.attendees);
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('attendees-list').innerHTML = '<p>Failed to load attendees</p>';
        });
    }
    
    // Function to update attendees list UI
    function updateAttendeesUI(attendees) {
        const attendeesList = document.getElementById('attendees-list');
        
        if (attendees && attendees.length > 0) {
            let html = '<ul class="attendees-grid">';
            
            attendees.forEach(attendee => {
                html += `
                    <li class="attendee-item">
                        <div class="attendee-avatar">
                            <img src="${attendee.avatar || '/static/media/default_avatar.png'}" alt="${attendee.name}">
                        </div>
                        <div class="attendee-info">
                            <span class="attendee-name">${attendee.name}</span>
                            <span class="attendee-status ${attendee.status.toLowerCase()}">${attendee.status}</span>
                        </div>
                    </li>
                `;
            });
            
            html += '</ul>';
            attendeesList.innerHTML = html;
        } else {
            attendeesList.innerHTML = '<p>No attendees yet. Be the first to RSVP!</p>';
        }
    }
    
    // Function to filter events based on search and filter criteria
    function filterEvents() {
        const searchTerm = searchInput.value.toLowerCase();
        const dateFilter = filterDate.value;
        const rsvpFilter = filterRsvp.value;
        
        const eventCards = document.querySelectorAll('.event-card');
        
        eventCards.forEach(card => {
            let visible = true;
            
            // Apply search filter
            if (searchTerm) {
                const title = card.querySelector('h3').textContent.toLowerCase();
                const description = card.querySelector('.event-description p').textContent.toLowerCase();
                const location = card.querySelector('.event-location').textContent.toLowerCase();
                const organizer = card.querySelector('.event-organizer').textContent.toLowerCase();
                
                if (!title.includes(searchTerm) && 
                    !description.includes(searchTerm) && 
                    !location.includes(searchTerm) && 
                    !organizer.includes(searchTerm)) {
                    visible = false;
                }
            }
            
            // Apply date filter
            if (visible && dateFilter !== 'all') {
                const dateText = card.querySelector('.event-date').textContent;
                const eventDate = new Date(dateText);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                
                const tomorrow = new Date(today);
                tomorrow.setDate(tomorrow.getDate() + 1);
                
                const nextWeek = new Date(today);
                nextWeek.setDate(nextWeek.getDate() + 7);
                
                const nextMonth = new Date(today);
                nextMonth.setMonth(nextMonth.getMonth() + 1);
                
                if (dateFilter === 'today' && (eventDate < today || eventDate >= tomorrow)) {
                    visible = false;
                } else if (dateFilter === 'week' && (eventDate < today || eventDate >= nextWeek)) {
                    visible = false;
                } else if (dateFilter === 'month' && (eventDate < today || eventDate >= nextMonth)) {
                    visible = false;
                }
            }
            
            // Apply RSVP filter
            if (visible && rsvpFilter !== 'all') {
                const rsvpStatus = card.querySelector('.rsvp-status');
                
                if (rsvpFilter === 'attending' && (!rsvpStatus || !rsvpStatus.classList.contains('yes'))) {
                    visible = false;
                } else if (rsvpFilter === 'maybe' && (!rsvpStatus || !rsvpStatus.classList.contains('maybe'))) {
                    visible = false;
                } else if (rsvpFilter === 'not-responded' && rsvpStatus) {
                    visible = false;
                }
            }
            
            // Show or hide the card
            card.style.display = visible ? '' : 'none';
        });
        
        // Check if we have any visible events
        const visibleEvents = document.querySelectorAll('.event-card[style=""]').length;
        const noEventsMessage = document.querySelector('.no-filtered-events');
        
        if (visibleEvents === 0) {
            if (!noEventsMessage) {
                const eventsGrid = document.querySelector('.events-grid');
                const message = document.createElement('div');
                message.className = 'no-filtered-events';
                message.innerHTML = '<p>No events match your filters. Please try different criteria.</p>';
                eventsGrid.insertAdjacentElement('afterend', message);
            }
        } else if (noEventsMessage) {
            noEventsMessage.remove();
        }
    }
    
    // Function to show notification
    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
});