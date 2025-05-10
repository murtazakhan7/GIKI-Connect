from rest_framework import serializers
from .models import (
    User, Student, Alumnus, Profile, Message,
    Notification, ConnectionRequest, JobPost, MentorshipMatch
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Student
        fields = '__all__'


class AlumnusSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Alumnus
        fields = '__all__'


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = '__all__'


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = '__all__'


class NotificationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'


class ConnectionRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = '__all__'


class JobPostSerializer(serializers.ModelSerializer):
    poster = AlumnusSerializer(read_only=True)

    class Meta:
        model = JobPost
        fields = '__all__'


class MentorshipMatchSerializer(serializers.ModelSerializer):
    mentor = AlumnusSerializer(read_only=True)
    mentee = StudentSerializer(read_only=True)

    class Meta:
        model = MentorshipMatch
        fields = '__all__'
