document.addEventListener('DOMContentLoaded', function() {
    // Show alert message
function showAlert(message) {
alert(message); 
}
// Toggle comments section
function toggleComments(postId) {
const commentsSection = document.getElementById('comments-' + postId);
const commentBtn = document.querySelector(`[data-post-id="${postId}"]`);

if (commentsSection.style.display === 'none' || !commentsSection.style.display) {
    commentsSection.style.display = 'block';
    commentBtn.classList.add('active');
} else {
    commentsSection.style.display = 'none';
    commentBtn.classList.remove('active');
}

}


// Add event listeners for comment toggle buttons
document.querySelectorAll('.comment-btn').forEach(button => {
button.addEventListener('click', function() {
    const postId = this.getAttribute('data-post-id');
    toggleComments(postId);
});
});

// Image preview for post creation
const mediaInput = document.querySelector('input[name="media_url"]');
if (mediaInput) {
mediaInput.addEventListener('change', function(event) {
    const file = event.target.files[0];
    const previewContainer = document.getElementById('media-preview-container');

    // Clear previous preview
    if (previewContainer) {
        previewContainer.innerHTML = '';
    }

    if (file) {
        // Check if it's an image
        if (!file.type.startsWith('image/')) {
            showAlert('Only image files are allowed.');
            mediaInput.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.createElement('div');
            preview.id = 'media-preview';
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Media Preview" class="img-preview">
                <button type="button" class="remove-preview-btn">&times;</button>
            `;

            if (previewContainer) {
                previewContainer.appendChild(preview);
            }

            const removeBtn = preview.querySelector('.remove-preview-btn');
            removeBtn.addEventListener('click', function() {
                mediaInput.value = '';
                previewContainer.innerHTML = '';
            });
        };
        reader.readAsDataURL(file);
    }
});

}

// Like post functionality
const likeForms = document.querySelectorAll('.like-form');
likeForms.forEach(form => {
form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const postId = this.getAttribute('data-post-id');
    const likeBtn = this.querySelector('button');
    const likeIcon = likeBtn.querySelector('i');
    const likeCountSpan = this.closest('.post-card').querySelector('.like-count');

    // Use fetch for AJAX request
    fetch(this.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `post_id=${postId}`
    })
    .then(response => response.json())
    .then(data => {
        // Update like button and count
        if (data.liked) {
            likeIcon.classList.remove('far');
            likeIcon.classList.add('fas');
        } else {
            likeIcon.classList.remove('fas');
            likeIcon.classList.add('far');
        }
        
        // Update like count
        likeCountSpan.textContent = `${data.like_count} likes`;
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Failed to like the post. Please try again.');
    });
});
});

// Add comment functionality
const commentForms = document.querySelectorAll('.comment-form');
commentForms.forEach(form => {
form.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const postId = this.getAttribute('data-post-id');
    const commentInput = this.querySelector('input[name="text"]');
    const commentText = commentInput.value.trim();
    const commentsContainer = document.getElementById(`comments-${postId}`);

    if (!commentText) return;

    // Use fetch for AJAX request
    fetch(this.action, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `post_id=${postId}&text=${encodeURIComponent(commentText)}`
    })
    .then(response => response.json())
    .then(data => {
        // Create new comment element
        const newComment = document.createElement('div');
        newComment.className = 'comment';
        newComment.innerHTML = `
            <div class="comment-avatar">
                <img src="${data.author_image}" alt="${data.author_name}">
            </div>
            <div class="comment-content">
                <div class="comment-header">
                    <span class="comment-user">${data.author_name}</span>
                    <span class="comment-time">Just now</span>
                </div>
                <p class="comment-text">${commentText}</p>
                <div class="comment-actions">
                    <span class="comment-action">Like</span>
                    <span class="comment-action">Reply</span>
                </div>
            </div>
        `;

        // Append new comment
        commentsContainer.insertBefore(newComment, commentsContainer.querySelector('.add-comment'));
        
        // Clear input
        commentInput.value = '';
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('Failed to post comment. Please try again.');
    });
});
});

// Enter key submission for comment input
const commentInputs = document.querySelectorAll('.add-comment-input');
commentInputs.forEach(input => {
input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        const form = this.closest('form');
        form.dispatchEvent(new Event('submit'));
    }
});
});
});