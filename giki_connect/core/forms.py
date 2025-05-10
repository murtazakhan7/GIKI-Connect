from django import forms
from .models import Group, Post, Comment, Event, EventAttendee

# Group Form
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'is_public']

# Post Form
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content_text', 'media_url']

# Comment Form
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

# Event Form
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'start', 'end', 'location', 'capacity']

# EventAttendee Form
class EventAttendeeForm(forms.ModelForm):
    class Meta:
        model = EventAttendee
        fields = ['rsvp_status']
