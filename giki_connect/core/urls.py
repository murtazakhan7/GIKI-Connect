from django.urls import path
from .views import (
    NotificationAPI,
    MentorshipMatchAPI,
    AcceptMentorshipAPI,
    MenteesListAPI,
    ShowMentorAPI,
    MessageAPI,
    JobPostAPI,
    AllJobPostsAPI,
    SignUpView,
    CreateProfileView,
    UpdateProfileView,
    GetProfileView,
    SendConnectionRequestAPI,
    ManageConnectionRequestAPI,
    ViewReceivedRequestsAPI,
    ViewConnectionsAPI
)

urlpatterns = [
    # Notification endpoints
    path('notifications/', NotificationAPI.as_view(), name='notifications_list'),
    path('notifications/<int:user_id>/', NotificationAPI.as_view(), name='user_notifications'),
    path('notifications/read/<int:pk>/', NotificationAPI.as_view(), name='mark_notification_read'),
    
    # Mentorship endpoints
    path('mentorship/match/', MentorshipMatchAPI.as_view(), name='mentorship_match'),
    path('mentorship/accept/<int:user_id>/', AcceptMentorshipAPI.as_view(), name='accept_mentorship'),
    path('mentorship/mentees/', MenteesListAPI.as_view(), name='mentees_list'),
    path('mentorship/mentor/<int:user_id>/', ShowMentorAPI.as_view(), name='show_mentor'),
    
    # Connection endpoints
    path('connections/send/<int:sender_id>/<int:receiver_id>/',  SendConnectionRequestAPI.as_view(),  name='send_connection_request'),
    path('connections/sent/<int:user_id>/', SendConnectionRequestAPI.as_view(), name='view_sent_requests'),
    path('connections/manage/<int:request_id>/', ManageConnectionRequestAPI.as_view(), name='manage_connection_request'),
    path('connections/received/<int:receiver_id>/', ViewReceivedRequestsAPI.as_view(), name='view_received_requests'),
    path('connections/list/<int:user_id>/', ViewConnectionsAPI.as_view(), name='view_all_connections'),
    
    # Message endpoints
    path('messages/', MessageAPI.as_view(), name='messages_list'),
    path('messages/send/<int:sender_id>/<int:receiver_id>/', MessageAPI.as_view(), name='send_message'),
    path('messages/received/<int:user_id>/', MessageAPI.as_view(http_method_names=['get']), {'method': 'get_received'}, name='received_messages'),
    path('messages/sent/<int:user_id>/', MessageAPI.as_view(http_method_names=['get']), {'method': 'get_sent'}, name='sent_messages'),
    
    # Job post endpoints
    path('jobs/', JobPostAPI.as_view(), name='jobs_list'),
    path('jobs/create/<int:user_id>/', JobPostAPI.as_view(), name='create_job'),
    path('jobs/all/', AllJobPostsAPI.as_view(), name='all_jobs'),
    
    # User and profile endpoints
    path('signup/', SignUpView.as_view(), name='signup'),
    path('profile/create/<int:user_id>/', CreateProfileView.as_view(), name='create_profile'),
    path('profile/update/<int:profile_id>/', UpdateProfileView.as_view(), name='update_profile'),
    path('profile/<int:profile_id>/', GetProfileView.as_view(), name='get_profile'),
]