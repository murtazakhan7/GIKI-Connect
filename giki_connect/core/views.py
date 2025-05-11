from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    User, Student, Alumnus, Profile, Notification, JobPost, 
   Alumnus, Student, MentorshipMatch, Connection, ConnectionRequest, Message, User, MentorshipApplication )
from .serializers import (
    UserSerializer, StudentSerializer, AlumnusSerializer, ProfileSerializer, NotificationSerializer, 
    JobPostSerializer, MentorshipApplicationSerializer,  MentorshipMatchSerializer, 
    ConnectionSerializer, ConnectionRequestSerializer, MessageSerializer, MentorshipApplicationSerializer, ConnectionRequestSerializer
)
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.timezone import now


class NotificationAPI(APIView):

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        notifications = Notification.objects.filter(user=user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    def post(self, request, pk=None):
        notification = get_object_or_404(Notification, pk=pk)
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})

class MentorshipMatchAPI(APIView):
    def post(self, request):
        action_type = request.data.get('action')

        if action_type == 'propose':
            mentor = get_object_or_404(Alumnus, user=request.user)
            mentee_id = request.data.get('mentee_id')
            mentee = get_object_or_404(Student, pk=mentee_id)
            match = MentorshipMatch.objects.create(mentor=mentor, mentee=mentee)
            Notification.objects.create(user=mentee.user, type="Mentorship", content=f"{request.user.name} wants to mentor you.")
            return Response(MentorshipMatchSerializer(match).data)

        elif action_type == 'apply':
            if hasattr(request.user, 'student'):
                app = MentorshipApplication.objects.create(student=request.user.student)
                return Response(MentorshipApplicationSerializer(app).data)
            return Response({"error": "Only students can apply."}, status=status.HTTP_403_FORBIDDEN)

        return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)


class AcceptMentorshipAPI(APIView):
    def post(self, request, user_id):
        mentor = get_object_or_404(Alumnus, user__id=user_id)
        match_id = request.data.get('match_id')
        match = get_object_or_404(MentorshipMatch, pk=match_id, mentor=mentor)

        match.status = 'Active'
        match.save()

        Connection.objects.create(user1=mentor.user, user2=match.mentee.user)

        return Response({"status": "Mentorship accepted"})

class MenteesListAPI(APIView):

    def get(self, request):
        if not hasattr(request.user, 'alumnus'):
            return Response({"error": "Only mentors can view mentees."}, status=status.HTTP_403_FORBIDDEN)

        matches = MentorshipMatch.objects.filter(mentor=request.user.alumnus, status='Active')
        serializer = MentorshipMatchSerializer(matches, many=True)
        return Response(serializer.data)
    

class ShowMentorAPI(APIView):

    def get(self, request, user_id):
        student = get_object_or_404(Student, user__id=user_id)
        match = get_object_or_404(MentorshipMatch, mentee=student, status='Active')
        return Response({"mentor": match.mentor.user.name})
    

class SendConnectionRequestAPI(APIView):
    """API view for sending connection requests and viewing sent requests"""
    
    def post(self, request, sender_id=None, receiver_id=None):
        """Send a connection request from sender to receiver"""
        to_user = get_object_or_404(User, pk=receiver_id)
        from_user = get_object_or_404(User, pk=sender_id)
        
        # Check if there's already a connection
        if Connection.objects.filter(user1=from_user, user2=to_user).exists() or \
           Connection.objects.filter(user1=to_user, user2=from_user).exists():
            return Response({"error": "You are already connected."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if there's already a pending connection request
        existing_request = ConnectionRequest.objects.filter(
            from_user=from_user, 
            to_user=to_user, 
            status='Pending'
        ).first()
        
        if existing_request:
            # Resend the notification for the existing request
            Notification.objects.create(
                user=to_user, 
                type="Connection", 
                content=f"Connection request by {from_user.name} (sent again)"
            )
            print(f"Connection request resent from {from_user.name} to {to_user.name}")
            return Response(ConnectionRequestSerializer(existing_request).data)
        
        # Create new connection request if none exists
        req = ConnectionRequest.objects.create(
            from_user=from_user, 
            to_user=to_user, 
            status='Pending', 
            requested_at=now()
        )
        Notification.objects.create(
            user=to_user, 
            type="Connection", 
            content=f"Connection request by {from_user.name}"
        )
        print(f"Connection request sent from {from_user.name} to {to_user.name}")
        return Response(ConnectionRequestSerializer(req).data)

    def get(self, request, user_id=None):
        """View all connection requests sent by a user"""
        sent_requests = ConnectionRequest.objects.filter(from_user__pk=user_id)
        serializer = ConnectionRequestSerializer(sent_requests, many=True)
        return Response(serializer.data)


class ManageConnectionRequestAPI(APIView):
    """API view for handling accept/reject connection requests"""
    
    def post(self, request, request_id=None):
        action = request.data.get('action', '')
        
        if action == 'accept':
            return self.accept_request(request, request_id)
        elif action == 'reject':
            return self.reject_request(request, request_id)
        
        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
    
    def accept_request(self, request, request_id):
        """Accept a connection request"""
        req = get_object_or_404(ConnectionRequest, pk=request_id, status='Pending')
        req.status = 'Accepted'
        req.save()
        
        # Create the connection between users

        Connection.objects.create(user1=req.from_user, user2=req.to_user)
        
        # Notify the sender that their request was accepted
        Notification.objects.create(
            user=req.from_user, 
            type="Connection", 
            content=f"{req.to_user.name} accepted your connection request."
        )
        
        return Response({"status": "Connection accepted."})
    
    def reject_request(self, request, request_id):
        """Reject a connection request"""
        req = get_object_or_404(ConnectionRequest, pk=request_id, status='Pending')
        req.status = 'Declined'
        req.save()
        
        return Response({"status": "Connection rejected."})


class ViewReceivedRequestsAPI(APIView):
    """API view for viewing received connection requests"""
    
    def get(self, request, receiver_id=None):
        """Get all pending connection requests for a user"""
        received_requests = ConnectionRequest.objects.filter(
            to_user__pk=receiver_id, 
            status='Pending'
        )
        serializer = ConnectionRequestSerializer(received_requests, many=True)
        return Response(serializer.data)


class ViewConnectionsAPI(APIView):
    """API view for viewing all connections of a user"""
    
    def get(self, request, user_id=None):
        """Get all connections for a user"""
        # Get connections where the user is either user1 or user2
        connections = Connection.objects.filter(user1__pk=user_id) | Connection.objects.filter(user2__pk=user_id)
        serializer = ConnectionSerializer(connections, many=True)
        return Response(serializer.data)
    

class MessageAPI(APIView):

    def get(self, request):
        messages = Message.objects.filter(sender=request.user) | Message.objects.filter(receiver=request.user)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def post(self, request, sender_id, receiver_id):
        # Check if the sender is the authenticated user
        if sender_id != request.user.id:
            return Response({"error": "You can only send messages from your own account."}, status=status.HTTP_403_FORBIDDEN)

        receiver = get_object_or_404(User, pk=receiver_id)

        # Check if there is a connection between sender and receiver
        if not Connection.objects.filter(user1=request.user, user2=receiver).exists() and \
           not Connection.objects.filter(user1=receiver, user2=request.user).exists():
            return Response({"error": "You are not connected with the receiver."}, status=status.HTTP_403_FORBIDDEN)

        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=request.data.get('content'),
            name=request.data.get('name'),
            description=request.data.get('description', ''),
            is_public=request.data.get('is_public', True)
        )

        # Create a notification for the receiver
        Notification.objects.create(
            user=receiver,
            type="Message",
            content=f"Message from {request.user.name} at {now().strftime('%H:%M %d/%m/%Y')}"
        )

        return Response(MessageSerializer(message).data)

    def get_received(self, request, user_id):
        # List all received messages for the given user_id
        if user_id != request.user.id:
            return Response({"error": "You can only see your own received messages."}, status=status.HTTP_403_FORBIDDEN)

        messages = Message.objects.filter(receiver=request.user)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def get_sent(self, request, user_id):
        # List all sent messages for the given user_id
        if user_id != request.user.id:
            return Response({"error": "You can only see your own sent messages."}, status=status.HTTP_403_FORBIDDEN)

        messages = Message.objects.filter(sender=request.user)
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)



class JobPostAPI(APIView):

    def get(self, request):
        jobposts = JobPost.objects.all()
        serializer = JobPostSerializer(jobposts, many=True)
        return Response(serializer.data)

    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(user, 'alumnus'):
            serializer = JobPostSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(poster=user.alumnus)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Only alumni can post jobs."}, status=status.HTTP_403_FORBIDDEN)


# Additional views for requirements
class AllJobPostsAPI(APIView):

    def get(self, request):
        jobposts = JobPost.objects.all()
        serializer = JobPostSerializer(jobposts, many=True)
        return Response(serializer.data)

class IncomingConnectionRequestsAPI(APIView):

    def get(self, request):
        requests = ConnectionRequest.objects.filter(to_user=request.user, status='Pending')
        serializer = ConnectionRequestSerializer(requests, many=True)
        return Response(serializer.data)


class SignUpView(APIView):
    def post(self, request):
        role = request.data.get('role')
        if role not in ['Student', 'Alumnus']:
            return Response({"error": "Invalid role specified."}, status=status.HTTP_400_BAD_REQUEST)

        request.data['password_hash'] = make_password(request.data['password_hash'])
        user_serializer = UserSerializer(data=request.data)

        if user_serializer.is_valid():
            user = user_serializer.save()
            if role == 'Student':
                student_data = request.data.get('student', {})
                student_data['user'] = user.user_id
                student_serializer = StudentSerializer(data=student_data)
                ##############
                if student_serializer.is_valid():
                    student_serializer.save()
                ##############
                else:
                    print(student_serializer.errors)
                    user.delete()
                    return Response(student_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            elif role == 'Alumnus':
                alumnus_data = request.data.get('alumnus', {})
                alumnus_data['user'] = user.user_id
                alumnus_serializer = AlumnusSerializer(data=alumnus_data)
                if alumnus_serializer.is_valid():
                    alumnus_serializer.save()
                ##############
                else:
                    user.delete()
                    return Response(alumnus_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            return Response(user_serializer.data, status=status.HTTP_201_CREATED)

        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateProfileView(APIView):
    def post(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            data = request.data.copy()
            data['user'] = user_id
            serializer = ProfileSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


class UpdateProfileView(APIView):
    def put(self, request, profile_id):
        try:
            profile = Profile.objects.get(profile_id=profile_id)
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)


class GetProfileView(APIView):
    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(profile_id=profile_id)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data)
        except Profile.DoesNotExist:
            return Response({"error": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
