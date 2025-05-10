from django.urls import path
from .views import (
    SignUpView,
    CreateProfileView,
    UpdateProfileView,
    GetProfileView
)
from django.urls import path
from . import views



urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),

    # Profile endpoints (based on profile_id)
    path('users/<int:user_id>/profiles/create/', CreateProfileView.as_view(), name='create-profile'),
    path('profiles/<int:profile_id>/update/', UpdateProfileView.as_view(), name='update-profile'),
    path('profiles/<int:profile_id>/', GetProfileView.as_view(), name='get-profile'),
    # path('create/group/', views.create_group, name='create_group'),
    # path('groups/', views.group_list, name='group_list'),

    # # Post URLs
    # path('create/post/', views.create_post, name='create_post'),
    # path('posts/', views.post_list, name='post_list'),
    # path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    # path('post/<int:post_id>/comment/', views.create_comment, name='create_comment'),

    # Event URLs
    path('create/event/', views.create_event, name='create_event'),
    path('events/', views.event_list, name='event_list'),
    path('event/<int:event_id>/rsvp/', views.rsvp_event, name='rsvp_event'),
]
