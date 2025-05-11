from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.models import Notification, JobPost, Alumnus, Student, MentorshipMatch, Connection, ConnectionRequest, Message, User
from core.serializers import NotificationSerializer, JobPostSerializer, MentorshipApplicationSerializer, MentorshipMatchSerializer, ConnectionSerializer, ConnectionRequestSerializer, MessageSerializer
