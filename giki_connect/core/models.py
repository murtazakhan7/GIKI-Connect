# models.py
from django.db import models

from django.utils import timezone
import uuid

class User(models.Model):
    ROLE_CHOICES = [
        ('Student', 'Student'),
        ('Alumnus', 'Alumnus'),
    ]

    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    mail = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=128)  # store hashed password
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role})"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    major = models.CharField(max_length=100)
    graduation_year = models.IntegerField()

class Alumnus(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    employer = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    mentoring_interest = models.BooleanField(default=False)

class Profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    skills = models.JSONField(default=list)  
    education = models.TextField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.name}"


class Group(models.Model):
    group_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)


class Message(models.Model):
    message_id = models.AutoField(primary_key=True)
    sender = models.ForeignKey('User', related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey('User', related_name='received_messages', on_delete=models.CASCADE, null=True, blank=True)
    group = models.ForeignKey('Group', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class GroupMember(models.Model):
    ROLE_CHOICES = [
        ('Member', 'Member'),
        ('Moderator', 'Moderator'),
    ]
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Member')
    joined_at = models.DateTimeField(auto_now_add=True)

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content_text = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.author.username} at {self.timestamp}"

class Comment(models.Model):
    comment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=255)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE)
    capacity = models.PositiveIntegerField()

    def __str__(self):
        return self.title

class EventAttendee(models.Model):
    RSVP_CHOICES = [
        ('Yes', 'Yes'),
        ('No', 'No'),
        ('Maybe', 'Maybe'),
    ]
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rsvp_status = models.CharField(max_length=10, choices=RSVP_CHOICES, default='Maybe')
