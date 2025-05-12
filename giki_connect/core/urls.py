from django.urls import path
from .views import ( NotificationAPI, StudentMentorshipAPI, AlumniMentorshipAPI, MentorshipStatusAPI, ShowMentorAPI, MessageView, 
                    SendMessageView, ViewMessage, JobPostAPI, EventListView, RSVPEventView, EventAttendeesView, 
                    EventUpdateView, SignUpView, CreateProfileView, UpdateProfileView, GetProfileView, SendConnectionRequestAPI, 
                    ManageConnectionRequestAPI, ViewReceivedRequestsAPI, ViewConnectionsAPI, GroupMessageView, ListGroupsView, 
                    CreateGroupView, JoinGroupView, MakeModeratorView, KickMemberView, ApprovedGroupsView, ApproveRequestView,  
                    CreatePostView, AllPostsView, UserPostsView, PostDetailView, DeletePostView, CommentAPI, PostCommentsAPI, 
                    SendConnectionRequestAPI, ManageConnectionRequestAPI, SignInView )

app_name = 'core'

urlpatterns = [
    # Notification endpoints
    path('notifications/<int:user_id>/', NotificationAPI.as_view(), name='user_notifications'),
    path('notifications/read/<int:pk>/', NotificationAPI.as_view(), name='mark_notification_read'),
    
    # Mentorship endpoints
    # Mentorship Application endpoints
    path('mentorship/apply/<int:user_id>/', StudentMentorshipAPI.as_view(), name='apply_for_mentorship'),
    path('mentorship/withdraw/<int:user_id>/', StudentMentorshipAPI.as_view(), name='withdraw_mentorship_application'),
    # Alumni mentorship endpoints
    path('mentorship/applications/<int:user_id>/', AlumniMentorshipAPI.as_view(), name='view_mentorship_applications'),
    path('mentorship/accept/<int:user_id>/<int:application_id>/', AlumniMentorshipAPI.as_view(), name='accept_mentorship'),
    # Mentorship status endpoints - for both students and alumni
    path('mentorship/status/<int:user_id>/', MentorshipStatusAPI.as_view(), name='view_active_mentorships'),
    path('mentorship/status/<int:user_id>/<int:match_id>/', MentorshipStatusAPI.as_view(), name='update_mentorship_status'),
    path('mentorship/getmentor/<int:user_id>/',ShowMentorAPI.as_view(), name='get_mentor'),

    # Event endpoints
    path('events/', EventListView.as_view(), name='list_events'),
    path('events/create/<int:user_id>/', EventListView.as_view(), name='create_event'),
    path('events/<int:event_id>/rsvp/', RSVPEventView.as_view(), name='rsvp_event'),
    path('events/<int:event_id>/attendees/', EventAttendeesView.as_view(), name='event_attendees'),
    path('events/<int:event_id>/update/', EventUpdateView.as_view(), name='update_event'),

    # Group endpoints
    path('group/join/<int:group_id>/', JoinGroupView.as_view(), name='join_group'),
    path('group/approve/<int:group_id>/<int:user_id>/', ApproveRequestView.as_view(), name='approve_request'),
    path('group/make_moderator/<int:group_id>/<int:user_id>/', MakeModeratorView.as_view(), name='make_moderator'),
    path('group/kick/<int:group_id>/<int:user_id>/', KickMemberView.as_view(), name='kick_member'),

    # Group messaging
    path('group/create/<int:user_id>/', CreateGroupView.as_view(), name='create_group'),
    path('group/message/<int:group_id>/<int:user_id>/', GroupMessageView.as_view(), name='group_message'),
    # Group listing and retrieval
    path('group/list/', ListGroupsView.as_view(), name='list_groups'),
    path('group/approved/<int:user_id>/', ApprovedGroupsView.as_view(), name='approved_groups'),
    
    # Connection endpoints
    path('connections/send/<int:sender_id>/<int:receiver_id>/',  SendConnectionRequestAPI.as_view(),  name='send_connection_request'),
    path('connections/sent/<int:user_id>/', SendConnectionRequestAPI.as_view(), name='view_sent_requests'),
    path('connections/manage/<int:request_id>/', ManageConnectionRequestAPI.as_view(), name='manage_connection_request'),
    path('connections/received/<int:receiver_id>/', ViewReceivedRequestsAPI.as_view(), name='view_received_requests'),
    path('connections/list/<int:user_id>/', ViewConnectionsAPI.as_view(), name='view_all_connections'),
    
    # Message endpoints
    path('messages/<int:user_id>/', MessageView.as_view(), name='list_messages'),  # List of users user can talk to
    path('messages/send/<int:message_id>/', SendMessageView.as_view(), name='send_message'),  # Add new message to chat
    path('messages/view/<int:message_id>/', ViewMessage.as_view(), name='view_message'),  # View full conversation

    # Job post endpoints - CHECK
    path('jobs/', JobPostAPI.as_view(), name='jobs_list'),
    path('jobs/create/<int:user_id>/', JobPostAPI.as_view(), name='create_job'),
    
    # post - CHECK
    path('posts/<int:user_id>/', CreatePostView.as_view(), name='create-post'),
    path('posts/', AllPostsView.as_view(), name='all-posts'),
    path('posts/user/<int:user_id>/', UserPostsView.as_view(), name='user-posts'),
    path('posts/<int:post_id>/details/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<int:post_id>/delete/<int:user_id>/', DeletePostView.as_view(), name='delete-post'),
    
    # Comments - CHECK (ONE BUG FOR COMMENT NOTIFICATION)
    path('comment/<int:post_id>/<int:user_id>/', CommentAPI.as_view(), name='add_comment'),
    path('comment/edit/<int:comment_id>/<int:user_id>/', CommentAPI.as_view(), name='edit_comment'),
    path('comment/delete/<int:comment_id>/<int:user_id>/', CommentAPI.as_view(), name='delete_comment'),
    path('comment/post/<int:post_id>/', PostCommentsAPI.as_view(), name='post_comments'),

    # User - CHECK
    path('signup/', SignUpView.as_view(), name='signup'),
    path('signin/', SignInView.as_view(), name='signin'),

    # PROFILES - CHECK
    path('profile/create/<int:user_id>/', CreateProfileView.as_view(), name='create_profile'),
    path('profile/update/<int:profile_id>/', UpdateProfileView.as_view(), name='update_profile'),
    path('profile/<int:user_id>/', GetProfileView.as_view(), name='get_profile'),
]