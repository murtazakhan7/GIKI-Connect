from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    User, Student, Alumnus, Profile, Notification, JobPost, 
   Alumnus, Student, MentorshipMatch, Connection, ConnectionRequest, Message, User, EventAttendee, Event,
   Group, GroupMember, MentorshipApplication )
from .serializers import (
    UserSerializer, StudentSerializer, AlumnusSerializer, ProfileSerializer, NotificationSerializer, 
    JobPostSerializer, MentorshipApplicationSerializer,  MentorshipMatchSerializer, 
    ConnectionSerializer, ConnectionRequestSerializer, MessageSerializer, EventAttendeeSerializer, EventSerializer,
     GroupMemberSerializer, GroupSerializer, MentorshipApplicationSerializer, ConnectionRequestSerializer
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



class EventListView(APIView):
    def get(self, request):
        events = Event.objects.all().order_by('-start')
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data)

class RSVPEventView(APIView):
    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        user = request.user

        if event.start <= now():
            return Response({"error": "Cannot RSVP to past events."}, status=400)

        if EventAttendee.objects.filter(event=event).count() >= event.capacity:
            return Response({"error": "Event capacity is full."}, status=400)

        if EventAttendee.objects.filter(event=event, user=user).exists():
            return Response({"error": "You have already RSVPed to this event."}, status=400)

        rsvp_status = request.data.get("rsvp_status", "Maybe")
        attendee = EventAttendee.objects.create(event=event, user=user, rsvp_status=rsvp_status)
        return Response(EventAttendeeSerializer(attendee).data, status=201)

    def put(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        user = request.user

        if event.start <= now():
            return Response({"error": "Cannot change RSVP for past events."}, status=400)

        attendee = get_object_or_404(EventAttendee, event=event, user=user)
        attendee.rsvp_status = request.data.get("rsvp_status", attendee.rsvp_status)
        attendee.save()
        return Response(EventAttendeeSerializer(attendee).data)

class EventAttendeesView(APIView):
    def get(self, request, event_id):
        attendees = EventAttendee.objects.filter(event_id=event_id)
        serializer = EventAttendeeSerializer(attendees, many=True)
        return Response(serializer.data)

class EventUpdateView(APIView):
    def put(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        if request.user != event.organizer:
            return Response({"error": "Only the event organizer can update this event."}, status=403)

        event.location = request.data.get("location", event.location)
        event.start = request.data.get("start", event.start)
        event.end = request.data.get("end", event.end)
        event.capacity = request.data.get("capacity", event.capacity)
        event.save()

        attendees = EventAttendee.objects.filter(event=event).exclude(user=request.user)
        for attendee in attendees:
            Notification.objects.create(
                user=attendee.user,
                type="Event",
                content=f"The event '{event.title}' has been updated."
            )

        return Response(EventSerializer(event).data)

class JoinGroupView(APIView):
    def post(self, request, group_id):
        user_id = request.data.get('user_id')
        user = User.objects.get(user_id=user_id)
        group = Group.objects.get(id=group_id)

        if group.is_public:
            GroupMember.objects.create(user=user, group=group, role="member", joined_at=now())
            return Response({"message": "Joined group successfully!"}, status=status.HTTP_201_CREATED)
        else:
            GroupMember.objects.create(user=user, group=group, role="pending_request")
            return Response({"message": "Request sent to join group. Awaiting moderator approval."}, status=status.HTTP_202_ACCEPTED)

# 2. Approve Member
class ApproveRequestView(APIView):
    def post(self, request, group_id, user_id):
        approver = request.user
        group = Group.objects.get(id=group_id)

        approver_member = GroupMember.objects.filter(user=approver, group=group, role="moderator").first()
        if not approver_member:
            return Response({"error": "Only moderators can approve requests."}, status=status.HTTP_403_FORBIDDEN)

        member = GroupMember.objects.filter(user_id=user_id, group=group, role="pending_request").first()
        if member:
            member.role = "member"
            member.joined_at = now()
            member.save()
            return Response({"message": "User approved successfully."})
        return Response({"error": "No pending request found."}, status=status.HTTP_404_NOT_FOUND)

# 3. Make Moderator
class MakeModeratorView(APIView):
    def post(self, request, group_id, user_id):
        actor = request.user
        group = Group.objects.get(id=group_id)

        if not GroupMember.objects.filter(user=actor, group=group, role="moderator").exists():
            return Response({"error": "Only moderators can promote."}, status=status.HTTP_403_FORBIDDEN)

        member = GroupMember.objects.filter(user_id=user_id, group=group, role="member").first()
        if member:
            member.role = "moderator"
            member.save()
            return Response({"message": "User promoted to moderator."})
        return Response({"error": "User is not eligible for promotion."}, status=status.HTTP_400_BAD_REQUEST)

# 4. Create Group
class CreateGroupView(APIView):
    def post(self, request, user_id):
        user = User.objects.get(user_id=user_id)
        data = request.data
        group = Group.objects.create(
            name=data.get('name'),
            description=data.get('description'),
            is_public=data.get('is_public', True)
        )
        GroupMember.objects.create(user=user, group=group, role="moderator", joined_at=now())
        return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)

# 5. Group Messaging
class GroupMessageView(APIView):
    def post(self, request, group_id, user_id):
        user = User.objects.get(user_id=user_id)
        group = Group.objects.get(id=group_id)

        membership = GroupMember.objects.filter(user=user, group=group).first()
        if not membership or membership.role == "pending_request":
            return Response({"error": "You must be a group member to message."}, status=status.HTTP_403_FORBIDDEN)

        message = request.data.get("message")
        if not message:
            return Response({"error": "Message cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        new_entry = {
            "sender_id": user.user_id,
            "message": message,
            "timestamp": str(now())
        }

        group.chat.append(new_entry)
        group.save()

        # Notify other members
        members = GroupMember.objects.filter(group=group).exclude(user=user)
        for m in members:
            Notification.objects.create(
                user=m.user,
                type="GroupMessage",
                content=f"New message in {group.name} from {user.name}"
            )

        return Response({"message": "Message sent!"})

# 6. List All Groups
class ListGroupsView(APIView):
    def get(self, request):
        groups = Group.objects.all()
        return Response(GroupSerializer(groups, many=True).data)

# 7. List My Approved Groups
class ApprovedGroupsView(APIView):
    def get(self, request, user_id):
        approved_groups = GroupMember.objects.filter(
            user_id=user_id, role__in=["moderator", "member"]
        ).values_list("group", flat=True)
        groups = Group.objects.filter(id__in=approved_groups)
        return Response(GroupSerializer(groups, many=True).data)

class KickMemberView(APIView):
    def post(self, request, group_id, user_id):
        actor = request.user
        group = Group.objects.get(id=group_id)

        if not GroupMember.objects.filter(user=actor, group=group, role="moderator").exists():
            return Response({"error": "Only moderators can kick members."}, status=status.HTTP_403_FORBIDDEN)

        GroupMember.objects.filter(user_id=user_id, group=group).delete()
        return Response({"message": "Member has been removed from the group."})


class StudentMentorshipAPI(APIView):
    """API for students to apply for mentorship"""
    
    def post(self, request, user_id=None):
        """Student applies for mentorship"""
        # Get the student based on user_id
        user = get_object_or_404(User, pk=user_id)
        student = get_object_or_404(Student, user=user)
        
        # Check if student already applied
        existing_application = MentorshipApplication.objects.filter(student=student).exists()
        if existing_application:
            return Response(
                {"error": "You have already applied for mentorship."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create application
        application = MentorshipApplication.objects.create(
            student=student,
            applied_at=now()
        )
        
        # Notify all alumni who have mentoring_interest=True
        interested_alumni = Alumnus.objects.filter(mentoring_interest=True)
        for alumnus in interested_alumni:
            Notification.objects.create(
                user=alumnus.user,
                type="Mentorship",
                content=f"New mentorship application from {user.name}"
            )
        
        return Response(
            MentorshipApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )
    
    def delete(self, request, user_id=None):
        """Student withdraws mentorship application"""
        user = get_object_or_404(User, pk=user_id)
        student = get_object_or_404(Student, user=user)
        application = get_object_or_404(MentorshipApplication, student=student)
        
        application.delete()
        return Response(
            {"message": "Your mentorship application has been withdrawn."},
            status=status.HTTP_200_OK
        )


class AlumniMentorshipAPI(APIView):
    """API for alumni to view and accept mentorship applications"""
    
    def get(self, request, user_id=None):
        """Get list of all students who have applied for mentorship"""
        # Verify the user is an alumnus
        user = get_object_or_404(User, pk=user_id)
        get_object_or_404(Alumnus, user=user)
        
        # Get all mentorship applications
        applications = MentorshipApplication.objects.all()
        students = [app.student for app in applications]
        
        # Return list of students with applications
        return Response(
            StudentSerializer(students, many=True).data,
            status=status.HTTP_200_OK
        )
    
    def post(self, request, user_id=None, application_id=None):
        """Accept a student as mentee based on application_id"""
        if not application_id:
            return Response(
                {"error": "Application ID is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the user is an alumnus
        user = get_object_or_404(User, pk=user_id)
        alumnus = get_object_or_404(Alumnus, user=user)
        
        # Get the application and associated student
        application = get_object_or_404(MentorshipApplication, pk=application_id)
        student = application.student
        
        # Create mentorship match
        match = MentorshipMatch.objects.create(
            mentor=alumnus,
            mentee=student,
            status='Active',
            created_at=now()
        )
        
        # Create connection between mentor and mentee
        Connection.objects.create(
            user1=user,
            user2=student.user,
            connected_at=now()
        )
        
        # Delete the application since it's been accepted
        application.delete()
        
        # Notify the student
        Notification.objects.create(
            user=student.user,
            type="Mentorship",
            content=f"{user.name} has accepted your mentorship application!"
        )
        
        return Response(
            MentorshipMatchSerializer(match).data,
            status=status.HTTP_201_CREATED
        )


class MentorshipStatusAPI(APIView):
    """API for handling active mentorships"""
    
    def get(self, request, user_id=None):
        """Get all active mentorships for user with user_id"""
        user = get_object_or_404(User, pk=user_id)
        
        # Try to get as student
        student = Student.objects.filter(user=user).first()
        if student:
            mentorships = MentorshipMatch.objects.filter(mentee=student)
            return Response(
                MentorshipMatchSerializer(mentorships, many=True).data,
                status=status.HTTP_200_OK
            )
        
        # Try to get as alumnus
        alumnus = Alumnus.objects.filter(user=user).first()
        if alumnus:
            mentorships = MentorshipMatch.objects.filter(mentor=alumnus)
            return Response(
                MentorshipMatchSerializer(mentorships, many=True).data,
                status=status.HTTP_200_OK
            )
        
        return Response(
            {"error": "User is neither student nor alumnus."}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    def post(self, request, user_id=None, match_id=None):
        """Update mentorship status (complete/cancel)"""
        if not match_id:
            return Response(
                {"error": "Match ID is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')
        if action not in ['complete', 'cancel']:
            return Response(
                {"error": "Valid actions are 'complete' or 'cancel'."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the user
        user = get_object_or_404(User, pk=user_id)
        
        # Get mentorship match
        match = get_object_or_404(MentorshipMatch, pk=match_id)
        
        # Verify current user is involved in this mentorship
        if match.mentor.user.user_id != user.user_id and match.mentee.user.user_id != user.user_id:
            return Response(
                {"error": "You are not involved in this mentorship."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update match status
        if action == 'complete':
            match.status = 'Completed'
        else:
            match.status = 'Cancelled'
        
        match.save()
        
        # Notify the other party
        other_user = match.mentee.user if user.user_id == match.mentor.user.user_id else match.mentor.user
        Notification.objects.create(
            user=other_user,
            type="Mentorship",
            content=f"Your mentorship has been {match.status.lower()}." 
        )
        
        return Response(
            MentorshipMatchSerializer(match).data,
            status=status.HTTP_200_OK
        )
    

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
    

class MessageView(APIView):
    
    def get(self, request, user_id):
        messages = Message.objects.filter(user1_id=user_id) | Message.objects.filter(user2_id=user_id)
        users = []
        for msg in messages:
            other_user = msg.user2 if msg.user1.id == int(user_id) else msg.user1
            users.append({
                "user": UserSerializer(other_user).data,
                "message_id": msg.id
            })
        return Response(users, status=status.HTTP_200_OK)

class SendMessageView(APIView):
    def post(self, request, message_id):
        message = get_object_or_404(Message, pk=message_id)
        sender_id = request.data.get("sender")
        msg_text = request.data.get("message")

        if not sender_id or not msg_text:
            return Response({"error": "Missing sender or message"}, status=status.HTTP_400_BAD_REQUEST)

        message.chat_history.append({
            "sender": sender_id,
            "message": msg_text,
            "timestamp": now().isoformat()
        })
        message.save()

        # Create a notification for the other user
        recipient = message.user2 if message.user1.id == int(sender_id) else message.user1
        Notification.objects.create(
            user=recipient,
            type="Message",
            content=f"New message from user {sender_id} at {now().strftime('%H:%M %d/%m/%Y')}"
        )

        return Response(MessageSerializer(message).data)

class ViewMessage(APIView):
    def get(self, request, message_id):
        message = get_object_or_404(Message, pk=message_id)
        return Response(MessageSerializer(message).data)


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
