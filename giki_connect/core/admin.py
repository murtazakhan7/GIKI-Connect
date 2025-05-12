from django.contrib import admin
from .models import (User, Student, Alumnus, Connection, MentorshipApplication, Profile, Event, JobPost, Comment, Post,
Notification, ConnectionRequest, Group, GroupMessage, GroupMember, Message, 
Mentorship, EventAttendee, EventUpdate, GroupRequest, GroupPost, GroupComment, GroupPostComment
)
admin.site.register(User)
admin.site.register(Student)
admin.site.register(Alumnus)
admin.site.register(MentorshipApplication)

