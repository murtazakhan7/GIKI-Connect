// groups_list.js
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabs = document.querySelectorAll('.groups-tab');
    const contents = document.querySelectorAll('.groups-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            // Add active class to current tab and content
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
});

// Modal functionality
function openCreateGroupModal() {
    document.getElementById('createGroupModal').style.display = 'block';
}

function closeCreateGroupModal() {
    document.getElementById('createGroupModal').style.display = 'none';
}

function openManageGroupModal(groupId) {
    // Here you would typically load group management content via AJAX
    document.getElementById('manageGroupModal').style.display = 'block';
    
    // For demonstration, we'll just set some placeholder content
    document.getElementById('manageGroupContent').innerHTML = `
        <h3>Group Management</h3>
        <p>Loading management options for group ${groupId}...</p>
        <div class="form-group">
            <button class="btn btn-outline" onclick="closeManageGroupModal()">Close</button>
        </div>
    `;
}

function closeManageGroupModal() {
    document.getElementById('manageGroupModal').style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target == document.getElementById('createGroupModal')) {
        closeCreateGroupModal();
    }
    if (event.target == document.getElementById('manageGroupModal')) {
        closeManageGroupModal();
    }
} 