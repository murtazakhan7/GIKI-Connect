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
    password_hash = models.CharField(max_length=128)  
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
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

class Connection(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_received')
    connected_at = models.DateTimeField(auto_now_add=True)
    
class MentorshipApplication(models.Model):
    application_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)

class Profile(models.Model):
    profile_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    skills = models.JSONField(default=list)  
    education = models.TextField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.name}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ('Message', 'Message'),
        ('Connection', 'Connection'),
        ('Event', 'Event'),
        ('Other', 'Other'),
    ]

    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.name} - {self.type}"

class ConnectionRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Declined', 'Declined'),
    ]

    request_id = models.AutoField(primary_key=True)
    from_user = models.ForeignKey('User', related_name='sent_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey('User', related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.from_user.name} -> {self.to_user.name} ({self.status})"

class JobPost(models.Model):
    job_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    poster = models.ForeignKey('Alumnus', on_delete=models.CASCADE)
    link = models.URLField()
    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.poster.user.name}"

class MentorshipMatch(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    match_id = models.AutoField(primary_key=True)
    mentor = models.ForeignKey('Alumnus', on_delete=models.CASCADE, related_name='mentorships_as_mentor')
    mentee = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='mentorships_as_mentee')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mentor: {self.mentor.user.name} | Mentee: {self.mentee.user.name} | Status: {self.status}"



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

    
class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=True)

    def _str_(self):
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
