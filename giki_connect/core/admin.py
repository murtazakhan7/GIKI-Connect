from django.contrib import admin
from .models import (
    User, Student, Alumnus, Connection, MentorshipApplication, Profile,
    Event, EventAttendee, Notification, Post, Comment, ConnectionRequest,
    JobPost, MentorshipMatch, Group, GroupMember, Message
)

admin.site.register(User)
admin.site.register(Student)
admin.site.register(Alumnus)
admin.site.register(Connection)
admin.site.register(MentorshipApplication)
admin.site.register(Profile)
admin.site.register(Event)
admin.site.register(EventAttendee)
admin.site.register(Notification)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(ConnectionRequest)
admin.site.register(JobPost)
admin.site.register(MentorshipMatch)
admin.site.register(Group)
admin.site.register(GroupMember)
admin.site.register(Message)
