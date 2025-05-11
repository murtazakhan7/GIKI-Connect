document.addEventListener('DOMContentLoaded', function() {
    const roleSelect = document.getElementById('role');
    const studentFields = document.getElementById('student-fields');
    const alumnusFields = document.getElementById('alumnus-fields');
    const userFields = document.getElementById('user-fields');
    const submitContainer = document.getElementById('submit-container');
    const form = document.querySelector('form');

    // Function to handle role selection
    function handleRoleChange() {
        const selectedRole = roleSelect.value;
        
        // Hide all role-specific fields first
        const allRoleFields = document.querySelectorAll('.role-specific-fields');
        allRoleFields.forEach(field => {
            field.style.display = 'none';
        });
        
        // Show specific fields based on role
        if (selectedRole === 'Student') {
            studentFields.style.display = 'block';
            userFields.style.display = 'block';
            submitContainer.style.display = 'block';
            
            // Make student fields required
            document.querySelectorAll('#student-fields input').forEach(input => {
                input.required = true;
            });
            // Make alumnus fields not required
            document.querySelectorAll('#alumnus-fields input').forEach(input => {
                input.required = false;
            });
            
        } else if (selectedRole === 'Alumnus') {
            alumnusFields.style.display = 'block';
            userFields.style.display = 'block';
            submitContainer.style.display = 'block';
            
            // Make alumnus fields required
            document.querySelectorAll('#alumnus-fields input').forEach(input => {
                input.required = true;
            });
            // Make student fields not required
            document.querySelectorAll('#student-fields input').forEach(input => {
                input.required = false;
            });
            
        } else if (selectedRole === 'Admin') {
            // Redirect to Django admin page
            window.location.href = '/admin/';
            return;
        } else {
            // No role selected, show only the role dropdown
            userFields.style.display = 'none';
            submitContainer.style.display = 'none';
        }
    }

    // Initialize form based on current selection
    handleRoleChange();
    
    // Listen for changes to the role selection
    roleSelect.addEventListener('change', handleRoleChange);
    
    // Form validation
    form.addEventListener('submit', function(event) {
        const selectedRole = roleSelect.value;
        
        // Validate password matching
        const password = document.getElementById('password_hash').value;
        const confirmPassword = document.getElementById('confirm_pass').value;
        
        if (password !== confirmPassword) {
            event.preventDefault();
            alert('Passwords do not match!');
            return;
        }
        
        // If Admin is selected, redirect instead of submitting the form
        if (selectedRole === 'Admin') {
            event.preventDefault();
            window.location.href = '/admin/';
        }
    });
});