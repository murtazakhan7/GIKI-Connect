from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import MultiPartParser, FormParser


from .models import (
    User, Student, Alumnus, Profile, Notification, JobPost, Post,
   Alumnus, Student, MentorshipMatch, Connection, ConnectionRequest, Message, User, EventAttendee, Event,
   Group, GroupMember, MentorshipApplication, Comment )
from .serializers import (
    UserSerializer, StudentSerializer, AlumnusSerializer, ProfileSerializer, NotificationSerializer, 
    JobPostSerializer, MentorshipApplicationSerializer,  MentorshipMatchSerializer, PostSerializer,
    ConnectionSerializer, ConnectionRequestSerializer, MessageSerializer, EventAttendeeSerializer, EventSerializer,
     GroupMemberSerializer, GroupSerializer, MentorshipApplicationSerializer, ConnectionRequestSerializer, CommentSerializer
)
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils.timezone import now


class NotificationAPI(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/notifications.html'

    def get(self, request, user_id=None):
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            notifications = Notification.objects.filter(user=user)
            serializer = NotificationSerializer(notifications, many=True)
            if request.accepted_renderer.format == 'html':
                return Response({'notifications': serializer.data}, template_name=self.template_name)
            return Response(serializer.data)
        else:
            # Render the empty page on GET requests without user_id
            return Response({}, template_name=self.template_name)

    def post(self, request, pk=None):
        notification = get_object_or_404(Notification, pk=pk)
        notification.is_read = True
        notification.save()
        if request.accepted_renderer.format == 'html':
            return Response({'status': 'marked as read'}, template_name=self.template_name)
        return Response({'status': 'marked as read'})

class SignInView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/sign_in.html'
    
    def get(self, request):
        # Render the empty form on GET requests
        return Response({}, template_name=self.template_name)
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            error = {"error": "Email and password are required."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            if check_password(password, user.password_hash):
                # Invalidate any previous session
                request.session.flush()
                # Set session for this user
                request.session['user_id'] = user.user_id
                
                # Check if user has profile
                has_profile = Profile.objects.filter(user=user).exists()
                
                if request.accepted_renderer.format == 'html':
                    if has_profile:
                        # Redirect to home page
                        return Response({
                            'user': UserSerializer(user).data,
                            'redirect': True,
                            'redirect_url': f'/api/profile/{user.user_id}/'
                        }, template_name=self.template_name)
                    else:
                        # Redirect to create profile
                        return Response({
                            'user': UserSerializer(user).data,
                            'redirect': True,
                            'redirect_url': f'/api/profile/create/{user.user_id}/'
                        }, template_name=self.template_name)
                return Response({"message": "Login successful", "user_id": user.user_id})
            else:
                error = {"error": "Invalid credentials."}
                if request.accepted_renderer.format == 'html':
                    return Response({'errors': error}, template_name=self.template_name)
                return Response(error, status=status.HTTP_401_UNAUTHORIZED)
                
        except User.DoesNotExist:
            error = {"error": "User with this email does not exist."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name)
            return Response(error, status=status.HTTP_404_NOT_FOUND)


class CommentAPI(APIView):

    def post(self, request, post_id, user_id):
        post = get_object_or_404(Post, pk=post_id)
        author = get_object_or_404(User, pk=user_id)
        data = request.data.copy()
        data['post'] = post.post_id
        data['author'] = author.user_id
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, comment_id, user_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author.user_id != user_id:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # updates timestamp automatically
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, comment_id, user_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author.user_id != user_id:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        comment.delete()
        return Response({'status': 'Comment deleted'}, status=status.HTTP_204_NO_CONTENT)

class PostCommentsAPI(APIView):
    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        comments = Comment.objects.filter(post=post).order_by('-timestamp')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)
    
class CreatePostView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, user_id):
        author = get_object_or_404(User, pk=user_id)
        data = request.data.copy()
        data['author'] = user_id
        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            post = serializer.save()

            # Notify other users
            users = User.objects.exclude(user_id=user_id)
            notifications = [
                Notification(
                    user=u,
                    type='Post',
                    content=f"{author.name} made a new post!"
                ) for u in users
            ]
            Notification.objects.bulk_create(notifications)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AllPostsView(APIView):
    def get(self, request):
        posts = Post.objects.all().order_by('-timestamp')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

class UserPostsView(APIView):
    def get(self, request, user_id):
        posts = Post.objects.filter(author__user_id=user_id).order_by('-timestamp')
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)

class PostDetailView(APIView):
    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        serializer = PostSerializer(post)
        return Response(serializer.data)

class DeletePostView(APIView):
    def delete(self, request, post_id, user_id):
        post = get_object_or_404(Post, pk=post_id)
        if post.author.user_id != user_id:
            return Response({"error": "You can only delete your own post."}, status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response({"message": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class EventListView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/event.html'
    
    def get(self, request):
        events = Event.objects.all().order_by('-start')
        serializer = EventSerializer(events, many=True)
        if request.accepted_renderer.format == 'html':
            return Response({'events': serializer.data}, template_name=self.template_name)
        return Response(serializer.data)
    
    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        data = request.data.copy()
        data['organizer'] = user.user_id
        serializer = EventSerializer(data=data)
        if serializer.is_valid():
            event = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RSVPEventView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/attend_event.html'
    
    def get(self, request, event_id=None):
        # Render the empty form on GET requests
        if event_id:
            event = get_object_or_404(Event, pk=event_id)
            event_data = EventSerializer(event).data
            return Response({'event': event_data}, template_name=self.template_name)
        return Response({}, template_name=self.template_name)
    
    def post(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        user = request.user

        if event.start <= now():
            error = {"error": "Cannot RSVP to past events."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=400)
            return Response(error, status=400)

        if EventAttendee.objects.filter(event=event).count() >= event.capacity:
            error = {"error": "Event capacity is full."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=400)
            return Response(error, status=400)

        if EventAttendee.objects.filter(event=event, user=user).exists():
            error = {"error": "You have already RSVPed to this event."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=400)
            return Response(error, status=400)

        rsvp_status = request.data.get("rsvp_status", "Maybe")
        attendee = EventAttendee.objects.create(event=event, user=user, rsvp_status=rsvp_status)
        attendee_data = EventAttendeeSerializer(attendee).data
        
        if request.accepted_renderer.format == 'html':
            return Response({'attendee': attendee_data}, template_name=self.template_name, status=201)
        return Response(attendee_data, status=201)

    def put(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        user = request.user

        if event.start <= now():
            error = {"error": "Cannot change RSVP for past events."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=400)
            return Response(error, status=400)

        attendee = get_object_or_404(EventAttendee, event=event, user=user)
        attendee.rsvp_status = request.data.get("rsvp_status", attendee.rsvp_status)
        attendee.save()
        
        attendee_data = EventAttendeeSerializer(attendee).data
        if request.accepted_renderer.format == 'html':
            return Response({'attendee': attendee_data}, template_name=self.template_name)
        return Response(attendee_data)

class EventAttendeesView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/event.html'
    
    def get(self, request, event_id=None):
        if event_id:
            attendees = EventAttendee.objects.filter(event_id=event_id)
            serializer = EventAttendeeSerializer(attendees, many=True)
            if request.accepted_renderer.format == 'html':
                return Response({'attendees': serializer.data}, template_name=self.template_name)
            return Response(serializer.data)
        return Response({}, template_name=self.template_name)

class EventUpdateView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/event.html'
    
    def get(self, request, event_id=None):
        if event_id:
            event = get_object_or_404(Event, pk=event_id)
            event_data = EventSerializer(event).data
            return Response({'event': event_data}, template_name=self.template_name)
        return Response({}, template_name=self.template_name)
    
    def put(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)

        if request.user != event.organizer:
            error = {"error": "Only the event organizer can update this event."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=403)
            return Response(error, status=403)

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

        event_data = EventSerializer(event).data
        if request.accepted_renderer.format == 'html':
            return Response({'event': event_data}, template_name=self.template_name)
        return Response(event_data)

class JoinGroupView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, group_id=None):
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            group_data = GroupSerializer(group).data
            return Response({'group': group_data}, template_name=self.template_name)
        return Response({}, template_name=self.template_name)
    
    def post(self, request, group_id):
        user_id = request.data.get('user_id')
        user = User.objects.get(user_id=user_id)
        group = Group.objects.get(id=group_id)

        if group.is_public:
            GroupMember.objects.create(user=user, group=group, role="member", joined_at=now())
            message = {"message": "Joined group successfully!"}
            if request.accepted_renderer.format == 'html':
                return Response({'success': message}, template_name=self.template_name, status=status.HTTP_201_CREATED)
            return Response(message, status=status.HTTP_201_CREATED)
        else:
            GroupMember.objects.create(user=user, group=group, role="pending_request")
            message = {"message": "Request sent to join group. Awaiting moderator approval."}
            if request.accepted_renderer.format == 'html':
                return Response({'success': message}, template_name=self.template_name, status=status.HTTP_202_ACCEPTED)
            return Response(message, status=status.HTTP_202_ACCEPTED)

# 2. Approve Member
class ApproveRequestView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, group_id=None, user_id=None):
        context = {}
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            context['group'] = GroupSerializer(group).data
            
            if user_id:
                member = GroupMember.objects.filter(user_id=user_id, group=group, role="pending_request").first()
                if member:
                    context['member'] = GroupMemberSerializer(member).data
        
        return Response(context, template_name=self.template_name)
    
    def post(self, request, group_id, user_id):
        approver = request.user
        group = Group.objects.get(id=group_id)

        approver_member = GroupMember.objects.filter(user=approver, group=group, role="moderator").first()
        if not approver_member:
            error = {"error": "Only moderators can approve requests."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_403_FORBIDDEN)
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        member = GroupMember.objects.filter(user_id=user_id, group=group, role="pending_request").first()
        if member:
            member.role = "member"
            member.joined_at = now()
            member.save()
            message = {"message": "User approved successfully."}
            if request.accepted_renderer.format == 'html':
                return Response({'success': message}, template_name=self.template_name)
            return Response(message)
            
        error = {"error": "No pending request found."}
        if request.accepted_renderer.format == 'html':
            return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_404_NOT_FOUND)
        return Response(error, status=status.HTTP_404_NOT_FOUND)

# 3. Make Moderator
class MakeModeratorView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, group_id=None, user_id=None):
        context = {}
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            context['group'] = GroupSerializer(group).data
            
            if user_id:
                member = GroupMember.objects.filter(user_id=user_id, group=group, role="member").first()
                if member:
                    context['member'] = GroupMemberSerializer(member).data
        
        return Response(context, template_name=self.template_name)
    
    def post(self, request, group_id, user_id):
        actor = request.user
        group = Group.objects.get(id=group_id)

        if not GroupMember.objects.filter(user=actor, group=group, role="moderator").exists():
            error = {"error": "Only moderators can promote."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_403_FORBIDDEN)
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        member = GroupMember.objects.filter(user_id=user_id, group=group, role="member").first()
        if member:
            member.role = "moderator"
            member.save()
            message = {"message": "User promoted to moderator."}
            if request.accepted_renderer.format == 'html':
                return Response({'success': message}, template_name=self.template_name)
            return Response(message)
            
        error = {"error": "User is not eligible for promotion."}
        if request.accepted_renderer.format == 'html':
            return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

# 4. Create Group
class CreateGroupView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, user_id=None):
        # Render the empty form on GET requests
        return Response({}, template_name=self.template_name)
    
    def post(self, request, user_id):
        user = User.objects.get(user_id=user_id)
        data = request.data
        group = Group.objects.create(
            name=data.get('name'),
            description=data.get('description'),
            is_public=data.get('is_public', True)
        )
        GroupMember.objects.create(user=user, group=group, role="moderator", joined_at=now())
        group_data = GroupSerializer(group).data
        
        if request.accepted_renderer.format == 'html':
            return Response({'group': group_data}, template_name=self.template_name, status=status.HTTP_201_CREATED)
        return Response(group_data, status=status.HTTP_201_CREATED)

# 5. Group Messaging
class GroupMessageView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/messages.html'
    
    def get(self, request, group_id=None, user_id=None):
        context = {}
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            context['group'] = GroupSerializer(group).data
            
            if group.chat:
                context['messages'] = group.chat
                
        return Response(context, template_name=self.template_name)
    
    def post(self, request, group_id, user_id):
        user = User.objects.get(user_id=user_id)
        group = Group.objects.get(id=group_id)

        membership = GroupMember.objects.filter(user=user, group=group).first()
        if not membership or membership.role == "pending_request":
            error = {"error": "You must be a group member to message."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_403_FORBIDDEN)
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        message = request.data.get("message")
        if not message:
            error = {"error": "Message cannot be empty."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

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
            
        response_data = {"message": "Message sent!"}
        if request.accepted_renderer.format == 'html':
            return Response({'success': response_data}, template_name=self.template_name)
        return Response(response_data)

# 6. List All Groups
class ListGroupsView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/group.html'
    
    def get(self, request):
        groups = Group.objects.all()
        groups_data = GroupSerializer(groups, many=True).data
        if request.accepted_renderer.format == 'html':
            return Response({'groups': groups_data}, template_name=self.template_name)
        return Response(groups_data)

# 7. List My Approved Groups
class ApprovedGroupsView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, user_id=None):
        if user_id:
            approved_groups = GroupMember.objects.filter(
                user_id=user_id, role__in=["moderator", "member"]
            ).values_list("group", flat=True)
            groups = Group.objects.filter(id__in=approved_groups)
            groups_data = GroupSerializer(groups, many=True).data
            if request.accepted_renderer.format == 'html':
                return Response({'groups': groups_data}, template_name=self.template_name)
            return Response(groups_data)
        return Response({}, template_name=self.template_name)

class KickMemberView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def post(self, request, group_id, user_id):
        actor = request.user
        group = Group.objects.get(id=group_id)

        if not GroupMember.objects.filter(user=actor, group=group, role="moderator").exists():
            error = {"error": "Only moderators can kick members."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_403_FORBIDDEN)
            return Response(error, status=status.HTTP_403_FORBIDDEN)

        GroupMember.objects.filter(user_id=user_id, group=group).delete()
        response_data = {"message": "Member has been removed from the group."}
        
        if request.accepted_renderer.format == 'html':
            return Response({'success': response_data}, template_name=self.template_name)
        return Response(response_data)


class StudentMentorshipAPI(APIView):
    """API for students to apply for mentorship"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, user_id=None):
        context = {}
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            student = Student.objects.filter(user=user).first()
            if student:
                # Check if student already has an application
                application = MentorshipApplication.objects.filter(student=student).first()
                if application:
                    context['application'] = MentorshipApplicationSerializer(application).data
        
        return Response(context, template_name=self.template_name)
    
    def post(self, request, user_id=None):
        """Student applies for mentorship"""
        # Get the student based on user_id
        user = get_object_or_404(User, pk=user_id)
        student = get_object_or_404(Student, user=user)
        
        # Check if student already applied
        existing_application = MentorshipApplication.objects.filter(student=student).exists()
        if existing_application:
            error = {"error": "You have already applied for mentorship."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        
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
                content=f"New mentorship application from {user.name}."
            )
        
        serializer = MentorshipApplicationSerializer(application)
        if request.accepted_renderer.format == 'html':
            return Response({'application': serializer.data}, template_name=self.template_name, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    def delete(self, request, user_id=None):
        """Student withdraws mentorship application"""
        # Get the student based on user_id
        user = get_object_or_404(User, pk=user_id)
        student = get_object_or_404(Student, user=user)
        
        # Find and delete application if it exists
        application = MentorshipApplication.objects.filter(student=student).first()
        if not application:
            error = {"error": "No active mentorship application found."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_404_NOT_FOUND)
            return Response(error, status=status.HTTP_404_NOT_FOUND)
        
        application.delete()
        
        response = {"status": "Application withdrawn successfully."}
        if request.accepted_renderer.format == 'html':
            return Response({'success': response}, template_name=self.template_name)
        return Response(response)


class AlumniMentorshipAPI(APIView):
    """API for alumni to view and accept mentorship applications"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, user_id=None, application_id=None):
        """Alumni views mentorship applications"""
        context = {}
        
        if user_id:
            # Get the alumnus based on user_id
            user = get_object_or_404(User, pk=user_id)
            alumnus = get_object_or_404(Alumnus, user=user)
            
            # Check if alumnus has mentoring interest
            if not alumnus.mentoring_interest:
                context['errors'] = {"error": "You have not expressed interest in mentoring."}
                return Response(context, template_name=self.template_name)
            
            # Get all mentorship applications
            applications = MentorshipApplication.objects.all()
            serializer = MentorshipApplicationSerializer(applications, many=True)
            context['applications'] = serializer.data
            
            if application_id:
                application = get_object_or_404(MentorshipApplication, pk=application_id)
                context['selected_application'] = MentorshipApplicationSerializer(application).data
        
        return Response(context, template_name=self.template_name)
    
    def post(self, request, user_id=None, application_id=None):
        """Alumni accepts a mentorship application"""
        # Get the alumnus based on user_id
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
        
        serializer = MentorshipMatchSerializer(match)
        if request.accepted_renderer.format == 'html':
            return Response({'match': serializer.data}, template_name=self.template_name, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MentorshipStatusAPI(APIView):
    """API for handling active mentorships"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, user_id=None, match_id=None):
        """Get all active mentorships for user with user_id"""
        context = {}
        
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            
            # Try to get as student
            student = Student.objects.filter(user=user).first()
            if student:
                mentorships = MentorshipMatch.objects.filter(mentee=student)
                serializer = MentorshipMatchSerializer(mentorships, many=True)
                context['mentorships'] = serializer.data
                context['role'] = 'student'
                
                if match_id:
                    match = get_object_or_404(MentorshipMatch, pk=match_id, mentee=student)
                    context['selected_match'] = MentorshipMatchSerializer(match).data
                
                if request.accepted_renderer.format == 'html':
                    return Response(context, template_name=self.template_name)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            # Try to get as alumnus
            alumnus = Alumnus.objects.filter(user=user).first()
            if alumnus:
                mentorships = MentorshipMatch.objects.filter(mentor=alumnus)
                serializer = MentorshipMatchSerializer(mentorships, many=True)
                context['mentorships'] = serializer.data
                context['role'] = 'alumnus'
                
                if match_id:
                    match = get_object_or_404(MentorshipMatch, pk=match_id, mentor=alumnus)
                    context['selected_match'] = MentorshipMatchSerializer(match).data
                
                if request.accepted_renderer.format == 'html':
                    return Response(context, template_name=self.template_name)
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            error = {"error": "User is neither student nor alumnus."}
            context['errors'] = error
            if request.accepted_renderer.format == 'html':
                return Response(context, template_name=self.template_name, status=status.HTTP_403_FORBIDDEN)
            return Response(error, status=status.HTTP_403_FORBIDDEN)
            
        return Response(context, template_name=self.template_name)
    
    def post(self, request, user_id=None, match_id=None):
        """Update mentorship status (complete/cancel)"""
        if not match_id:
            error = {"error": "Match ID is required."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        
        action = request.data.get('action')
        if action not in ['complete', 'cancel']:
            error = {"error": "Valid actions are 'complete' or 'cancel'."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        
        # Get the user
        user = get_object_or_404(User, pk=user_id)
        
        # Get mentorship match
        match = get_object_or_404(MentorshipMatch, pk=match_id)
        
        # Verify current user is involved in this mentorship
        if match.mentor.user.user_id != user.user_id and match.mentee.user.user_id != user.user_id:
            error = {"error": "You are not involved in this mentorship."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_403_FORBIDDEN)
            return Response(error, status=status.HTTP_403_FORBIDDEN)
        
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
        
        serializer = MentorshipMatchSerializer(match)
        if request.accepted_renderer.format == 'html':
            return Response({'match': serializer.data}, template_name=self.template_name)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ShowMentorAPI(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'

    def get(self, request, user_id=None):
        if not user_id:
            return Response({}, template_name=self.template_name)
            
        try:
            student = get_object_or_404(Student, user__id=user_id)
            match = get_object_or_404(MentorshipMatch, mentee=student, status='Active')
            mentor_data = {"mentor": match.mentor.user.name}
            if request.accepted_renderer.format == 'html':
                return Response({'mentor': mentor_data}, template_name=self.template_name)
            return Response(mentor_data)
        except:
            if request.accepted_renderer.format == 'html':
                return Response({'errors': {'error': 'No active mentor found.'}}, template_name=self.template_name)
            return Response({'error': 'No active mentor found.'}, status=404)


class SendConnectionRequestAPI(APIView):
    """API view for sending connection requests and viewing sent requests"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, sender_id=None, receiver_id=None, user_id=None):
        """View all connection requests sent by a user or render empty form"""
        if user_id:
            sent_requests = ConnectionRequest.objects.filter(from_user__pk=user_id)
            serializer = ConnectionRequestSerializer(sent_requests, many=True)
            if request.accepted_renderer.format == 'html':
                return Response({'requests': serializer.data}, template_name=self.template_name)
            return Response(serializer.data)
        else:
            # Render the empty form on GET requests
            return Response({}, template_name=self.template_name)
    
    def post(self, request, sender_id=None, receiver_id=None):
        """Send a connection request from sender to receiver"""
        to_user = get_object_or_404(User, pk=receiver_id)
        from_user = get_object_or_404(User, pk=sender_id)
        
        # Check if there's already a connection
        if Connection.objects.filter(user1=from_user, user2=to_user).exists() or \
           Connection.objects.filter(user1=to_user, user2=from_user).exists():
            error = {"error": "You are already connected."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        
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
            request_data = ConnectionRequestSerializer(existing_request).data
            if request.accepted_renderer.format == 'html':
                return Response({'request': request_data}, template_name=self.template_name)
            return Response(request_data)
        
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
        request_data = ConnectionRequestSerializer(req).data
        if request.accepted_renderer.format == 'html':
            return Response({'request': request_data}, template_name=self.template_name)
        return Response(request_data)


class ManageConnectionRequestAPI(APIView):
    """API view for handling accept/reject connection requests"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, request_id=None):
        context = {}
        if request_id:
            connection_request = get_object_or_404(ConnectionRequest, pk=request_id)
            context['request'] = ConnectionRequestSerializer(connection_request).data
        return Response(context, template_name=self.template_name)
    
    def post(self, request, request_id=None):
        action = request.data.get('action', '')
        
        if action == 'accept':
            return self.accept_request(request, request_id)
        elif action == 'reject':
            return self.reject_request(request, request_id)
        
        error = {"error": "Invalid action"}
        if request.accepted_renderer.format == 'html':
            return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
        return Response(error, status=status.HTTP_400_BAD_REQUEST)
    
    def accept_request(self, request, request_id):
        """Accept a connection request"""
        req = get_object_or_404(ConnectionRequest, pk=request_id, status='Pending')
        req.status = 'Accepted'
        req.save()
        
        # Create the connection between users
        Connection.objects.create(user1=req.from_user, user2=req.to_user)
        
        # Notify the requester
        Notification.objects.create(
            user=req.from_user, 
            type="Connection", 
            content=f"{req.to_user.name} accepted your connection request."
        )
        
        response = {"status": "Connection accepted."}
        if request.accepted_renderer.format == 'html':
            return Response({'success': response}, template_name=self.template_name)
        return Response(response)
    
    def reject_request(self, request, request_id):
        """Reject a connection request"""
        req = get_object_or_404(ConnectionRequest, pk=request_id, status='Pending')
        req.status = 'Declined'
        req.save()
        
        response = {"status": "Connection rejected."}
        if request.accepted_renderer.format == 'html':
            return Response({'success': response}, template_name=self.template_name)
        return Response(response)


class ViewReceivedRequestsAPI(APIView):
    """API view for viewing received connection requests"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, receiver_id=None):
        """Get all pending connection requests for a user"""
        context = {}
        
        if receiver_id:
            received_requests = ConnectionRequest.objects.filter(
                to_user__pk=receiver_id, 
                status='Pending'
            )
            serializer = ConnectionRequestSerializer(received_requests, many=True)
            context['requests'] = serializer.data
            
        if request.accepted_renderer.format == 'html':
            return Response(context, template_name=self.template_name)
        
        # If no receiver_id, return empty response for JSON
        if not receiver_id:
            return Response([])
            
        return Response(context.get('requests', []))


class ViewConnectionsAPI(APIView):
    """API view for viewing all connections of a user"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'
    
    def get(self, request, user_id=None):
        """Get all connections for a user"""
        context = {}
        
        if user_id:
            # Get connections where the user is either user1 or user2
            connections = Connection.objects.filter(user1__pk=user_id) | Connection.objects.filter(user2__pk=user_id)
            serializer = ConnectionSerializer(connections, many=True)
            context['connections'] = serializer.data
            
        if request.accepted_renderer.format == 'html':
            return Response(context, template_name=self.template_name)
            
        # If no user_id, return empty response for JSON
        if not user_id:
            return Response([])
            
        return Response(context.get('connections', []))


class MessageView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/messages.html'
    
    def get(self, request, user_id=None):
        context = {}
        
        if user_id:
            messages = Message.objects.filter(user1_id=user_id) | Message.objects.filter(user2_id=user_id)
            users = []
            for msg in messages:
                other_user = msg.user2 if msg.user1.id == int(user_id) else msg.user1
                users.append({
                    "user": UserSerializer(other_user).data,
                    "message_id": msg.id
                })
            context['users'] = users
            
        if request.accepted_renderer.format == 'html':
            return Response(context, template_name=self.template_name)
            
        # If no user_id, return empty response for JSON
        if not user_id:
            return Response([])
            
        return Response(context.get('users', []), status=status.HTTP_200_OK)

class ViewMessage(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/messages.html'
    
    def get(self, request, message_id=None):
        context = {}
        
        if message_id:
            message = get_object_or_404(Message, pk=message_id)
            message_data = MessageSerializer(message).data
            context['message'] = message_data
            
        if request.accepted_renderer.format == 'html':
            return Response(context, template_name=self.template_name)
            
        # If no message_id, return empty response for JSON
        if not message_id:
            return Response({})
            
        return Response(context.get('message', {}))


class SendMessageView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/messages.html'
    
    def get(self, request, message_id=None):
        context = {}
        if message_id:
            message = get_object_or_404(Message, pk=message_id)
            context['message'] = MessageSerializer(message).data
        return Response(context, template_name=self.template_name)
    
    def post(self, request, message_id):
        message = get_object_or_404(Message, pk=message_id)
        sender_id = request.data.get("sender")
        msg_text = request.data.get("message")

        if not sender_id or not msg_text:
            error = {"error": "Missing sender or message"}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

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

        message_data = MessageSerializer(message).data
        if request.accepted_renderer.format == 'html':
            return Response({'message': message_data}, template_name=self.template_name)
        return Response(message_data)

class JobPostAPI(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/post.html'

    def get(self, request, user_id=None):
        context = {}
        jobposts = JobPost.objects.all()
        context['jobposts'] = JobPostSerializer(jobposts, many=True).data
        
        if user_id:
            try:
                user = User.objects.get(pk=user_id)
                if hasattr(user, 'alumnus'):
                    context['alumnus'] = AlumnusSerializer(user.alumnus).data
            except User.DoesNotExist:
                pass
                
        return Response(context, template_name=self.template_name)

    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            error = {"error": "User not found."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_404_NOT_FOUND)
            return Response(error, status=status.HTTP_404_NOT_FOUND)

        if hasattr(user, 'alumnus'):
            serializer = JobPostSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(poster=user.alumnus)
                if request.accepted_renderer.format == 'html':
                    return Response({'jobpost': serializer.data}, template_name=self.template_name, status=status.HTTP_201_CREATED)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            if request.accepted_renderer.format == 'html':
                return Response({'errors': serializer.errors}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        error = {"error": "Only alumni can post jobs."}
        if request.accepted_renderer.format == 'html':
            return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_403_FORBIDDEN)
        return Response(error, status=status.HTTP_403_FORBIDDEN)


# Additional views for requirements
class AllJobPostsAPI(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/post.html'

    def get(self, request):
        jobposts = JobPost.objects.all()
        serializer = JobPostSerializer(jobposts, many=True)
        if request.accepted_renderer.format == 'html':
            return Response({'jobposts': serializer.data, 'title': 'All Job Postings'}, template_name=self.template_name)
        return Response(serializer.data)

class IncomingConnectionRequestsAPI(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/connections.html'

    def get(self, request):
        requests = ConnectionRequest.objects.filter(to_user=request.user, status='Pending')
        serializer = ConnectionRequestSerializer(requests, many=True)
        if request.accepted_renderer.format == 'html':
            return Response({'requests': serializer.data, 'title': 'Incoming Connection Requests'}, template_name=self.template_name)
        return Response(serializer.data)


class SignUpView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/signup.html'
    
    def get(self, request):
        # Check if this is a login request
        if request.path.endswith('/signin/'):
            return Response({}, template_name='core/sign_in.html')
        # Otherwise it's a signup request
        return Response({}, template_name=self.template_name)
        
    def post(self, request):
        # Handle signin
        if request.path.endswith('/signin/'):
            email = request.data.get('email')
            password = request.data.get('password')
            
            try:
                user = User.objects.get(email=email)
                
                # Check if password matches
                if not check_password(password, user.password_hash):
                    error = {"error": "Invalid password."}
                    if request.accepted_renderer.format == 'html':
                        return Response({'errors': error}, template_name='core/sign_in.html')
                    return Response(error, status=status.HTTP_401_UNAUTHORIZED)
                
                # Check if user has profile
                has_profile = Profile.objects.filter(user=user).exists()
                
                if has_profile:
                    # Redirect to home page
                    user_data = UserSerializer(user).data
                    if request.accepted_renderer.format == 'html':
                        return Response({'user': user_data, 'redirect': True, 'redirect_url': f'/api/profile/{user.user_id}/'}, 
                                        template_name='core/sign_in.html')
                    return Response(user_data)
                else:
                    # Redirect to create profile
                    if request.accepted_renderer.format == 'html':
                        return Response({'user': UserSerializer(user).data, 'redirect': True, 
                                        'redirect_url': f'/api/profile/create/{user.user_id}/'}, 
                                        template_name='core/sign_in.html')
                    return Response(UserSerializer(user).data)
                
            except User.DoesNotExist:
                error = {"error": "User with this email does not exist."}
                if request.accepted_renderer.format == 'html':
                    return Response({'errors': error}, template_name='core/sign_in.html')
                return Response(error, status=status.HTTP_404_NOT_FOUND)
        
        # Handle signup
        data = request.data.copy()  # Make a mutable copy
        role = data.get('role')
        
        if role not in ['Student', 'Alumnus']:
            errors = {"error": "Invalid role specified."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': errors}, template_name=self.template_name)
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        data['password_hash'] = make_password(data.get('password_hash', ''))
        user_serializer = UserSerializer(data=data)

        if user_serializer.is_valid():
            user = user_serializer.save()
            
            if role == 'Student':
                student_data = data.get('student', {})
                student_data['user'] = user.user_id
                student_serializer = StudentSerializer(data=student_data)
                
                if student_serializer.is_valid():
                    student_serializer.save()
                else:
                    user.delete()
                    errors = student_serializer.errors
                    if request.accepted_renderer.format == 'html':
                        return Response({'errors': errors}, template_name=self.template_name)
                    return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            elif role == 'Alumnus':
                alumnus_data = data.get('alumnus', {})
                alumnus_data['user'] = user.user_id
                alumnus_serializer = AlumnusSerializer(data=alumnus_data)
                
                if alumnus_serializer.is_valid():
                    alumnus_serializer.save()
                else:
                    user.delete()
                    errors = alumnus_serializer.errors
                    if request.accepted_renderer.format == 'html':
                        return Response({'errors': errors}, template_name=self.template_name)
                    return Response(errors, status=status.HTTP_400_BAD_REQUEST)

            # Redirect to profile creation page
            if request.accepted_renderer.format == 'html':
                return Response({
                    'user': user_serializer.data, 
                    'redirect': True,
                    'redirect_url': f'/api/profile/create/{user.user_id}/'
                }, template_name=self.template_name)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)

        if request.accepted_renderer.format == 'html':
            return Response({'errors': user_serializer.errors}, template_name=self.template_name)
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CreateProfileView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/profile.html'
    
    def get(self, request, user_id=None):
        context = {}
        if user_id:
            try:
                user = User.objects.get(user_id=user_id)
                context['user'] = UserSerializer(user).data
            except User.DoesNotExist:
                context['errors'] = {"error": "User not found."}
        return Response(context, template_name=self.template_name)
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(user_id=user_id)
            data = request.data.copy()
            data['user'] = user_id
            serializer = ProfileSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                if request.accepted_renderer.format == 'html':
                    return Response({'profile': serializer.data}, template_name=self.template_name, status=status.HTTP_201_CREATED)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            if request.accepted_renderer.format == 'html':
                return Response({'errors': serializer.errors}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except User.DoesNotExist:
            error = {"error": "User not found."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_404_NOT_FOUND)
            return Response(error, status=status.HTTP_404_NOT_FOUND)


class UpdateProfileView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/profile.html'
    
    def get(self, request, profile_id=None):
        context = {}
        if profile_id:
            try:
                profile = Profile.objects.get(profile_id=profile_id)
                serializer = ProfileSerializer(profile)
                context['profile'] = serializer.data
            except Profile.DoesNotExist:
                context['errors'] = {"error": "Profile not found."}
        return Response(context, template_name=self.template_name)
    
    def put(self, request, profile_id):
        try:
            profile = Profile.objects.get(profile_id=profile_id)
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                if request.accepted_renderer.format == 'html':
                    return Response({'profile': serializer.data}, template_name=self.template_name)
                return Response(serializer.data)
                
            if request.accepted_renderer.format == 'html':
                return Response({'errors': serializer.errors}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Profile.DoesNotExist:
            error = {"error": "Profile not found."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_404_NOT_FOUND)
            return Response(error, status=status.HTTP_404_NOT_FOUND)


class GetProfileView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/profile.html'
    
    def get(self, request, profile_id=None):
        if profile_id:
            try:
                profile = Profile.objects.get(profile_id=profile_id)
                serializer = ProfileSerializer(profile)
                if request.accepted_renderer.format == 'html':
                    return Response({'profile': serializer.data}, template_name=self.template_name)
                return Response(serializer.data)
            except Profile.DoesNotExist:
                error = {"error": "Profile not found."}
                if request.accepted_renderer.format == 'html':
                    return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_404_NOT_FOUND)
                return Response(error, status=status.HTTP_404_NOT_FOUND)
        return Response({}, template_name=self.template_name)
