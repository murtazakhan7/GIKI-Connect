document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show active tab content
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById(`${tabName}-event${tabName === 'manage' ? 's' : ''}`).classList.add('active');
        });
    });
    
    // Handle "Create Your First Event" button click
    const createTabTrigger = document.querySelector('.create-tab-trigger');
    if (createTabTrigger) {
        createTabTrigger.addEventListener('click', () => {
            // Switch to create event tab
            tabButtons.forEach(btn => btn.classList.remove('active'));
            document.querySelector('[data-tab="create"]').classList.add('active');
            
            tabContents.forEach(content => content.classList.remove('active'));
            document.getElementById('create-event').classList.add('active');
        });
    }
    
    // Modal functionality
    const modal = document.getElementById('update-modal');
    const closeModal = document.querySelector('.close-modal');
    const updateButtons = document.querySelectorAll('.btn-update');
    
    // Open modal with event data for updating
    updateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const eventId = this.getAttribute('data-event-id');
            
            // In a real application, you would fetch event details from the server
            // For now, we'll simulate this with dummy data or data from the DOM
            const eventCard = this.closest('.event-card');
            const title = eventCard.querySelector('h3').textContent;
            
            // Set values in the update form
            document.getElementById('update-event-id').value = eventId;
            document.getElementById('update-title').value = title;
            
            // Additional fields would be populated here in a real application
            // This would typically be done via an AJAX call to get full event details
            
            // Show modal
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent scrolling behind modal
        });
    });
    
    // Close modal when clicking the X
    if (closeModal) {
        closeModal.addEventListener('click', function() {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    });
    
    // Handle cancel event buttons
    const cancelButtons = document.querySelectorAll('.btn-cancel');
    cancelButtons.forEach(button => {
        button.addEventListener('click', function() {
            const eventId = this.getAttribute('data-event-id');
            
            if (confirm('Are you sure you want to cancel this event?')) {
                // Send request to cancel event
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = './event/cancel';
                
                // Add CSRF token
                const csrfInput = document.createElement('input');
                csrfInput.type = 'hidden';
                csrfInput.name = 'csrfmiddlewaretoken';
                csrfInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
                form.appendChild(csrfInput);
                
                // Add event ID
                const eventIdInput = document.createElement('input');
                eventIdInput.type = 'hidden';
                eventIdInput.name = 'event_id';
                eventIdInput.value = eventId;
                form.appendChild(eventIdInput);
                
                // Submit form
                document.body.appendChild(form);
                form.submit();
            }
        });
    });
    
    // Form validation
    const createForm = document.querySelector('.event-form');
    const updateForm = document.getElementById('update-event-form');
    
    [createForm, updateForm].forEach(form => {
        if (form) {
            form.addEventListener('submit', function(event) {
                // Get form inputs
                const title = form.querySelector('[name="title"]').value.trim();
                const description = form.querySelector('[name="description"]').value.trim();
                const start = new Date(form.querySelector('[name="start"]').value);
                const end = new Date(form.querySelector('[name="end"]').value);
                const capacity = parseInt(form.querySelector('[name="capacity"]').value);
                
                let isValid = true;
                let errorMessage = '';
                
                // Check if title is empty
                if (title === '') {
                    isValid = false;
                    errorMessage = 'Please enter an event title.';
                }
                
                // Check if description is too short
                else if (description.length < 10) {
                    isValid = false;
                    errorMessage = 'Please provide a more detailed description (at least 10 characters).';
                }
                
                // Check if start date is in the past
                else if (start < new Date()) {
                    isValid = false;
                    errorMessage = 'Start date cannot be in the past.';
                }
                
                // Check if end date is before start date
                else if (end <= start) {
                    isValid = false;
                    errorMessage = 'End date must be after start date.';
                }
                
                // Check if capacity is valid
                else if (isNaN(capacity) || capacity < 1) {
                    isValid = false;
                    errorMessage = 'Please enter a valid capacity (at least 1).';
                }
                
                // Show error or submit form
                if (!isValid) {
                    event.preventDefault();
                    alert(errorMessage);
                }
            });
        }
    });
    
    // Date-time input enhancements
    const dateTimeInputs = document.querySelectorAll('input[type="datetime-local"]');
    dateTimeInputs.forEach(input => {
        // Set minimum date to today
        const today = new Date();
        const year = today.getFullYear();
        const month = String(today.getMonth() + 1).padStart(2, '0');
        const day = String(today.getDate()).padStart(2, '0');
        const hours = String(today.getHours()).padStart(2, '0');
        const minutes = String(today.getMinutes()).padStart(2, '0');
        
        input.min = `${year}-${month}-${day}T${hours}:${minutes}`;
    });
});