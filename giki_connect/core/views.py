from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q

from django.shortcuts import get_object_or_404
from core.models import User, Post, Comment
from core.serializers import PostSerializer, UserSerializer
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

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
from django.db.utils import IntegrityError
from django.db.models import Q





class NotificationAPI(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/notifications.html'

    def get(self, request, user_id=None):
        if user_id:
            user = get_object_or_404(User, pk=user_id)
            notifications = Notification.objects.filter(user=user)
            serializer = NotificationSerializer(notifications, many=True)
            if request.accepted_renderer.format == 'html':
                # look up logged-in user
                session_uid = request.session.get('user_id')
                logged_in_user = None
                if session_uid:
                    logged_in_user = get_object_or_404(User, pk=session_uid)

                # build context including existing keys plus user
                context = {
                    'notifications': serializer.data,
                    'user': UserSerializer(logged_in_user).data if logged_in_user else None,
                }
                return Response(context, template_name=self.template_name)
            return Response(serializer.data)
        else:
            # Render the empty page on GET requests without user_id
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # build context including existing keys plus user
            context = {
                'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            }
            return Response(context, template_name=self.template_name)

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
        # Check if this is a logout request
        if request.path.endswith('/logout/'):
            # Clear the session
            request.session.flush()
            # Redirect to sign in page
            if request.accepted_renderer.format == 'html':
                return Response({'redirect': True, 'redirect_url': '/api/signin/'}, template_name=self.template_name)
            return Response({"message": "Logged out successfully"})
            
        # Render the empty form on GET requests
        # look up logged-in user
        session_uid = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        # build context including existing keys plus user
        context = {
            'user': UserSerializer(logged_in_user).data if logged_in_user else None,
        }
        return Response(context, template_name=self.template_name)
    
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
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_posts.html'
    
    def post(self, request, post_id, user_id):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(pk=user_id)
                post = Post.objects.get(pk=post_id)
                author = post.author
                comment = serializer.save(author=user, post=post)
                
                # Create and save notification
                notification = Notification(
                    user=author,
                    type='Other',
                    content=f"{user.name} Just wrote a new Comment!"
                )
                notification.save()
                
                if request.accepted_renderer.format == 'html':
                    # Redirect back to post detail
                    return Response({
                        'success': True,
                        'redirect': True,
                        'redirect_url': f'/api/posts/{post_id}/details/'
                    }, template_name=self.template_name)
                return Response(serializer.data, status=201)
            except User.DoesNotExist:
                error = {'error': 'User not found'}
                if request.accepted_renderer.format == 'html':
                    return Response({'errors': error}, template_name=self.template_name)
                return Response(error, status=404)
            except Post.DoesNotExist:
                error = {'error': 'Post not found'}
                if request.accepted_renderer.format == 'html':
                    return Response({'errors': error}, template_name=self.template_name)
                return Response(error, status=404)
        
        if request.accepted_renderer.format == 'html':
            return Response({'errors': serializer.errors}, template_name=self.template_name)
        return Response(serializer.errors, status=400)

    def put(self, request, comment_id, user_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author.user_id != user_id:
            error = {'error': 'Permission denied'}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name)
            return Response(error, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CommentSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # updates timestamp automatically
            if request.accepted_renderer.format == 'html':
                return Response({
                    'success': True,
                    'comment': serializer.data
                }, template_name=self.template_name)
            return Response(serializer.data)
        
        if request.accepted_renderer.format == 'html':
            return Response({'errors': serializer.errors}, template_name=self.template_name)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, comment_id, user_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        if comment.author.user_id != user_id:
            error = {'error': 'Permission denied'}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name)
            return Response(error, status=status.HTTP_403_FORBIDDEN)
        
        comment.delete()
        if request.accepted_renderer.format == 'html':
            return Response({
                'success': True,
                'message': 'Comment deleted'
            }, template_name=self.template_name)
        return Response({'status': 'Comment deleted'}, status=status.HTTP_204_NO_CONTENT)


class PostCommentsAPI(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_posts.html'
    
    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        comments = Comment.objects.filter(post=post).order_by('-timestamp')
        serializer = CommentSerializer(comments, many=True)
        
        if request.accepted_renderer.format == 'html':
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # build context including existing keys plus user
            context = {
                'post': PostSerializer(post).data,
                'comments': serializer.data,
                'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            }
            return Response(context, template_name=self.template_name)
        return Response(serializer.data)


class CreatePostView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_posts.html'
    
    def get(self, request, user_id):
        # For displaying the form
        user = get_object_or_404(User, pk=user_id)
        
        # look up logged-in user
        session_uid = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        # build context including existing keys plus user
        context = {
            'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            'profile_user': UserSerializer(user).data,
        }
        return Response(context, template_name=self.template_name)
    
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

            if request.accepted_renderer.format == 'html':
                return Response({
                    'success': True,
                    'post': serializer.data,
                    'redirect': True,
                    'redirect_url': f'/api/posts/{post.post_id}/details/'
                }, template_name=self.template_name)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if request.accepted_renderer.format == 'html':
            return Response({
                'errors': serializer.errors,
                'user': UserSerializer(author).data
            }, template_name=self.template_name)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class AllPostsView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'core/unified_posts.html'
    
#     def get(self, request):
#         posts = Post.objects.all().order_by('-timestamp')
#         serializer = PostSerializer(posts, many=True)
        
#         if request.accepted_renderer.format == 'html':
#             # Add comment counts for each post
#             posts_with_comments = []
#             for post_data in serializer.data:
#                 comment_count = Comment.objects.filter(post_id=post_data['post_id']).count()
#                 post_data['comment_count'] = comment_count
#                 posts_with_comments.append(post_data)
            
#             return Response({
#                 'posts': posts_with_comments
#             }, template_name=self.template_name)
#         return Response(serializer.data)


class AllPostsView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_posts.html'

    def get(self, request):
        # Fetch all posts and annotate with comment_count
        posts = Post.objects.all().order_by('-timestamp')
        serializer = PostSerializer(posts, many=True)
        posts_with_comments = []
        for post_data in serializer.data:
            post_data['comment_count'] = Comment.objects.filter(
                post_id=post_data['post_id']
            ).count()
            posts_with_comments.append(post_data)

        if request.accepted_renderer.format == 'html':
            # Retrieve current user from session (or None)
            user_obj = None
            user_id = request.session.get('user_id')
            if user_id:
                user_obj = get_object_or_404(User, pk=user_id)

            return Response({
                'posts': posts_with_comments,
                'user': UserSerializer(user_obj).data if user_obj else None
            }, template_name=self.template_name)

        # JSON API path
        return Response(serializer.data)


class UserPostsView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_posts.html'
    
    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        posts = Post.objects.filter(author__user_id=user_id).order_by('-timestamp')
        serializer = PostSerializer(posts, many=True)
        
        if request.accepted_renderer.format == 'html':
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # Add comment counts for each post
            posts_with_comments = []
            for post_data in serializer.data:
                comment_count = Comment.objects.filter(post_id=post_data['post_id']).count()
                post_data['comment_count'] = comment_count
                posts_with_comments.append(post_data)
            
            # build context including existing keys plus user
            context = {
                'profile_user': UserSerializer(user).data,
                'posts': posts_with_comments,
                'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            }
            return Response(context, template_name=self.template_name)
        return Response(serializer.data)


class PostDetailView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_posts.html'
    
    def get(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        comments = Comment.objects.filter(post=post).order_by('-timestamp')
        
        if request.accepted_renderer.format == 'html':
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # build context including existing keys plus user
            context = {
                'post': PostSerializer(post).data,
                'comments': CommentSerializer(comments, many=True).data,
                'comment_count': comments.count(),
                'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            }
            return Response(context, template_name=self.template_name)
        return Response(PostSerializer(post).data)


class DeletePostView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_posts.html'
    
    def get(self, request, post_id, user_id):
        # Show confirmation page
        post = get_object_or_404(Post, pk=post_id)
        if post.author.user_id != user_id:
            error = {"error": "You can only delete your own post."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name)
            return Response(error, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'post': PostSerializer(post).data,
            'confirm_delete': True
        }, template_name=self.template_name)
    
    def delete(self, request, post_id, user_id):
        post = get_object_or_404(Post, pk=post_id)
        if post.author.user_id != user_id:
            error = {"error": "You can only delete your own post."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name)
            return Response(error, status=status.HTTP_403_FORBIDDEN)
        
        post.delete()
        if request.accepted_renderer.format == 'html':
            return Response({
                'success': True,
                'message': 'Post deleted successfully.',
                'redirect': True,
                'redirect_url': '/api/posts/'
            }, template_name=self.template_name)
        return Response({"message": "Post deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

class EventListView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/event.html'
    
    def get(self, request):
        events = Event.objects.all().order_by('-start')
        serializer = EventSerializer(events, many=True)
        if request.accepted_renderer.format == 'html':
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # build context including existing keys plus user
            context = {
                'events': serializer.data,
                'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            }
            return Response(context, template_name=self.template_name)
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
    
    def get(self, request, event_id=None, user_id=None):
        # Render the empty form on GET requests
        if event_id:
            event = get_object_or_404(Event, pk=event_id)
            event_data = EventSerializer(event).data
            
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # build context including existing keys plus user
            context = {
                'event': event_data,
                'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            }
            return Response(context, template_name=self.template_name)
            
        # look up logged-in user
        session_uid = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        # build context including existing keys plus user
        context = {
            'user': UserSerializer(logged_in_user).data if logged_in_user else None,
        }
        return Response(context, template_name=self.template_name)
    
    def post(self, request, event_id, user_id):
        event = get_object_or_404(Event, pk=event_id)
        user = User.objects.get(user_id=user_id)

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

    def put(self, request, event_id, user_id):
        event = get_object_or_404(Event, pk=event_id)
        user = User.objects.get(user_id=user_id)

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
                # look up logged-in user
                session_uid = request.session.get('user_id')
                logged_in_user = None
                if session_uid:
                    logged_in_user = get_object_or_404(User, pk=session_uid)

                # build context including existing keys plus user
                context = {
                    'attendees': serializer.data,
                    'user': UserSerializer(logged_in_user).data if logged_in_user else None,
                }
                return Response(context, template_name=self.template_name)
            return Response(serializer.data)
            
        # look up logged-in user
        session_uid = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        # build context including existing keys plus user
        context = {
            'user': UserSerializer(logged_in_user).data if logged_in_user else None,
        }
        return Response(context, template_name=self.template_name)

class EventUpdateView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/event.html'
    
    def get(self, request, event_id=None, user_id=None):
        if event_id:
            event = get_object_or_404(Event, pk=event_id)
            event_data = EventSerializer(event).data
            
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # build context including existing keys plus user
            context = {
                'event': event_data,
                'user': UserSerializer(logged_in_user).data if logged_in_user else None,
            }
            return Response(context, template_name=self.template_name)
            
        # look up logged-in user
        session_uid = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        # build context including existing keys plus user
        context = {
            'user': UserSerializer(logged_in_user).data if logged_in_user else None,
        }
        return Response(context, template_name=self.template_name)
    
    def put(self, request, event_id, user_id):
        event = get_object_or_404(Event, pk=event_id)
        user = User.objects.get(user_id=user_id)

        if user.user_id != event.organizer.user_id:
            error = {"error": "Only the event organizer can update this event."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=403)
            return Response(error, status=403)

        event.location = request.data.get("location", event.location)
        event.start = request.data.get("start", event.start)
        event.end = request.data.get("end", event.end)
        event.capacity = request.data.get("capacity", event.capacity)
        event.save()

        attendees = EventAttendee.objects.filter(event=event).exclude(user=user.user_id)
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
    template_name = 'core/unified_connections.html'
    
    def get(self, request, group_id=None):
        if group_id:
            group = get_object_or_404(Group, pk=group_id)
            group_data = GroupSerializer(group).data
            
            # look up logged-in user
            session_uid = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

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
    template_name = 'core/unified_connections.html'
    
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
        approver = User.objects.get(user_id=user_id)
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
    template_name = 'core/unified_connections.html'
    
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
        actor = User.objects.get(user_id=user_id)
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
    template_name = 'core/unified_connections.html'
    
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
    template_name = 'core/groups_list.html'
    
    def get(self, request):
        groups = Group.objects.all()
        groups_data = GroupSerializer(groups, many=True).data
        if request.accepted_renderer.format == 'html':
            return Response({'groups': groups_data}, template_name=self.template_name)
        return Response(groups_data)

# 7. List My Approved Groups
class ApprovedGroupsView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_connections.html'
    
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
    template_name = 'core/unified_connections.html'
    
    def post(self, request, group_id, user_id):
        actor = User.objects.get(user_id=user_id)
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
    template_name = 'core/unified_connections.html'
    
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
    template_name = 'core/unified_connections.html'
    
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
    template_name = 'core/unified_connections.html'
    
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
    template_name = 'core/unified_connections.html'

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
    template_name = 'core/unified_connections.html'
    
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
        """Send a connection request from sender to receiver or handle DELETE via POST"""
        # Check if this is a DELETE request masquerading as POST
        if request.data.get('_method') == 'DELETE':
            return self.delete(request, sender_id, receiver_id)
            
        # If both sender_id and receiver_id are provided but receiver_id is 0,
        # this might be a cancellation request
        if sender_id and receiver_id == 0 and 'to_user_id' in request.data:
            try:
                receiver_id = int(request.data.get('to_user_id'))
            except (ValueError, TypeError):
                error = {"error": "Invalid receiver ID"}
                if request.accepted_renderer.format == 'html':
                    return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_400_BAD_REQUEST)
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
        
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
        
    def delete(self, request, sender_id=None, receiver_id=None):
        """Cancel a connection request"""
        from_user = get_object_or_404(User, pk=sender_id)
        to_user = get_object_or_404(User, pk=receiver_id)
        
        # Find and delete the pending request
        request_to_cancel = ConnectionRequest.objects.filter(
            from_user=from_user,
            to_user=to_user,
            status='Pending'
        ).first()
        
        if request_to_cancel:
            request_to_cancel.status = 'Cancelled'
            request_to_cancel.save()
            
            response = {"status": "Connection request cancelled."}
            if request.accepted_renderer.format == 'html':
                return Response({
                    'success': response,
                    'redirect': True,
                    'redirect_url': f'/api/profile/{to_user.user_id}/'
                }, template_name=self.template_name)
            return Response(response)
        else:
            error = {"error": "No pending connection request found."}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name, status=status.HTTP_404_NOT_FOUND)
            return Response(error, status=status.HTTP_404_NOT_FOUND)


class ManageConnectionRequestAPI(APIView):
    """API view for handling accept/reject connection requests"""
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_connections.html'
    
    def get(self, request, request_id=None):
        context = {}
        if request_id:
            connection_request = get_object_or_404(ConnectionRequest, pk=request_id)
            context['request'] = ConnectionRequestSerializer(connection_request).data
        return Response(context, template_name=self.template_name)
    
    def post(self, request, request_id=None):
        action = request.data.get('action', '')
        
        if action == 'accept':
            Message.objects.create(
                user1=ConnectionRequest.objects.get(pk=request_id).from_user,
                user2=ConnectionRequest.objects.get(pk=request_id).to_user,
                chat_history=[]
            )
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
    template_name = 'core/unified_connections.html'
    
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
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/unified_connections.html'

    def get(self, request, user_id):
        # 1. Profile user whose page we’re viewing
        profile_user = get_object_or_404(User, pk=user_id)

        # 2. Fetch actual connections (either side)
        connections = Connection.objects.filter(
            Q(user1=profile_user) | Q(user2=profile_user)
        )
        conn_data = ConnectionSerializer(connections, many=True).data

        # 3. Pending & sent connection requests
        sent_qs    = ConnectionRequest.objects.filter(from_user=profile_user, status='PENDING')
        pending_qs = ConnectionRequest.objects.filter(to_user=profile_user, status='PENDING')
        sent_data    = ConnectionSerializer(sent_qs, many=True).data
        pending_data = ConnectionSerializer(pending_qs, many=True).data

        # 4. “Suggestions” placeholder (customize with your real logic)
        suggestions_qs  = User.objects.exclude(pk=profile_user.pk)[:10]
        suggestion_data = UserSerializer(suggestions_qs, many=True).data

        # 5. Logged-in user lookup
        session_uid    = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        if request.accepted_renderer.format == 'html':
            context = {
                'connections':            conn_data,
                'sent_requests':          sent_data,
                'pending_requests':       pending_data,
                'suggestions':            suggestion_data,
                'pending_requests_count': pending_qs.count(),
                'sent_requests_count':    sent_qs.count(),
                'user': (
                    UserSerializer(logged_in_user).data
                    if logged_in_user else None
                ),
            }
            return Response(context, template_name=self.template_name)

        # JSON fallback
        return Response({
            'connections':      conn_data,
            'sent_requests':    sent_data,
            'pending_requests': pending_data,
            'suggestions':      suggestion_data,
        })


class MessageView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/messages.html'

    def get(self, request, user_id=None):
        users = []
        if user_id:
            # 1. grab all messages involving this user, ordered by newest first
            msgs = Message.objects.filter(
                Q(user1_id=user_id) | Q(user2_id=user_id)
            ).order_by('-message_id')  # or use a timestamp field if available

            seen = set()
            for msg in msgs:
                # identify the other participant
                if msg.user1_id == int(user_id):
                    other = msg.user2
                else:
                    other = msg.user1

                # add only the first occurrence of each other user
                if other.pk not in seen:
                    seen.add(other.pk)
                    users.append({
                        'user':       UserSerializer(other).data,
                        'message_id': msg.message_id,
                    })

        # lookup logged-in user
        session_uid    = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        if request.accepted_renderer.format == 'html':
            context = {
                'users': users,
                'user': (
                    UserSerializer(logged_in_user).data
                    if logged_in_user else None
                ),
            }
            return Response(context, template_name=self.template_name)

        # JSON fallback
        return Response(users, status=status.HTTP_200_OK)
# class MessageView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'core/messages.html'

#     def get(self, request, user_id=None):
#         # 1. Build list of chat threads for the profile user
#         users = []
#         if user_id:
#             msgs = Message.objects.filter(
#                 Q(user1_id=user_id) | Q(user2_id=user_id)
#             ).distinct('message_id')
#             for msg in msgs:
#                 other = msg.user2 if msg.user1.user_id == int(user_id) else msg.user1
#                 users.append({
#                     'user':       UserSerializer(other).data,
#                     'message_id': msg.message_id,
#                 })

#         # 2. Logged-in user lookup
#         session_uid    = request.session.get('user_id')
#         logged_in_user = None
#         if session_uid:
#             logged_in_user = get_object_or_404(User, pk=session_uid)

#         if request.accepted_renderer.format == 'html':
#             context = {
#                 'users': users,
#                 'user': (
#                     UserSerializer(logged_in_user).data
#                     if logged_in_user else None
#                 ),
#             }
#             return Response(context, template_name=self.template_name)

#         # JSON fallback
#         return Response(users, status=status.HTTP_200_OK)


class ViewMessage(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/messages.html'
    
    def get(self, request, message_id=None):
        if not message_id:
            # JSON fallback for no message_id
            return Response({})

        # Fetch the message data
        message_obj  = get_object_or_404(Message, pk=message_id)
        message_data = MessageSerializer(message_obj).data

        if request.accepted_renderer.format == 'html':
            # ── lookup logged-in user ──
            session_uid    = request.session.get('user_id')
            logged_in_user = None
            if session_uid:
                logged_in_user = get_object_or_404(User, pk=session_uid)

            # ── build context ──
            context = {
                'message': message_data,
                'user': (
                    UserSerializer(logged_in_user).data
                    if logged_in_user else None
                ),
            }
            return Response(context, template_name=self.template_name)

        # JSON response
        return Response(message_data)
# class SendMessageView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'core/messages.html'

#     def get(self, request, message_id=None):
#         context = {}
#         if message_id:
#             msg_obj        = get_object_or_404(Message, pk=message_id)
#             context['message'] = MessageSerializer(msg_obj).data

#         # Add logged-in user for template
#         session_uid    = request.session.get('user_id')
#         logged_in_user = None
#         if session_uid:
#             logged_in_user = get_object_or_404(User, pk=session_uid)

#         if request.accepted_renderer.format == 'html':
#             context['user'] = (
#                 UserSerializer(logged_in_user).data
#                 if logged_in_user else None
#             )
#             return Response(context, template_name=self.template_name)

#         return Response(context, status=status.HTTP_200_OK)

#     def post(self, request, message_id, user_id=None):
#         msg_obj = get_object_or_404(Message, pk=message_id)
#         sender  = get_object_or_404(User, pk=user_id)
#         # Who’s the other participant?
#         receiver = msg_obj.user2 if msg_obj.user1_id == sender.user_id else msg_obj.user1
#         text     = request.data.get("message")

#         if not text:
#             error = {"error": "Missing message text"}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name,
#                                 status=status.HTTP_400_BAD_REQUEST)
#             return Response(error, status=status.HTTP_400_BAD_REQUEST)

#         # Append chat history
#         msg_obj.chat_history.append({
#             "sender":    sender.name,
#             "sender_id": sender.user_id,
#             "message":   text,
#             "timestamp": now().isoformat()
#         })
#         msg_obj.save()

#         # Notify the other user
#         Notification.objects.create(
#             user=receiver,
#             type="Message",
#             content=f"New message from {sender.name} at {now().strftime('%H:%M %d/%m/%Y')}"
#         )

#         return Response(MessageSerializer(msg_obj).data)

class SendMessageView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/messages.html'

    def get(self, request, message_id=None):
        context = {}
        if message_id:
            msg_obj = get_object_or_404(Message, pk=message_id)
            context['message'] = MessageSerializer(msg_obj).data

        session_uid = request.session.get('user_id')
        logged_in_user = None
        if session_uid:
            logged_in_user = get_object_or_404(User, pk=session_uid)

        if request.accepted_renderer.format == 'html':
            context['user'] = (
                UserSerializer(logged_in_user).data
                if logged_in_user else None
            )
            return Response(context, template_name=self.template_name)

        return Response(context, status=status.HTTP_200_OK)

    def post(self, request, message_id):
        # Fetch message thread
        msg_obj = get_object_or_404(Message, pk=message_id)
        # Infer sender from session
        sender_id = request.session.get('user_id')
        sender = get_object_or_404(User, pk=sender_id)
        # Determine receiver
        receiver = msg_obj.user2 if msg_obj.user1_id == sender.user_id else msg_obj.user1
        text = request.data.get('message')

        if not text:
            error = {"error": "Missing message text"}
            if request.accepted_renderer.format == 'html':
                return Response({'errors': error}, template_name=self.template_name,
                                status=status.HTTP_400_BAD_REQUEST)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # Append chat history
        msg_obj.chat_history.append({
            "sender":    sender.name,
            "sender_id": sender.user_id,
            "message":   text,
            "timestamp": now().isoformat()
        })
        msg_obj.save()

        # Create notification
        Notification.objects.create(
            user=receiver,
            type="Message",
            content=f"New message from {sender.name} at {now().strftime('%H:%M %d/%m/%Y')}"
        )

        return Response(MessageSerializer(msg_obj).data)
    
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


from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.shortcuts import redirect
from rest_framework import status
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render,redirect
from core.models import User, Student, Alumnus



class SignUpView(APIView):
    template_name = 'core/signup.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # Grab the form fields
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password_hash', '').strip()
        name     = request.POST.get('name', '').strip()
        role     = request.POST.get('role', '').strip()

        errors = {}

        # 1) Basic validation
        if not all([email, password, name, role]):
            errors['all'] = "All fields are required."
        elif role not in ['Student', 'Alumnus']:
            errors['role'] = "Role must be Student or Alumnus."
        elif User.objects.filter(email=email).exists():
            errors['email'] = "A user with that email already exists."

        if errors:
            # Re‑render the form with errors and the previously entered data
            return render(request, self.template_name, {
                'errors':   errors,
                'prefill': {
                    'email': email,
                    'name': name,
                    'role': role,
                    # note: we *never* prefill passwords
                }
            })

        # 2) Create the User
        user = User.objects.create(
            name=name,
            email=email,
            password_hash=make_password(password),
            role=role
        )

        # 3) Create role‐specific record
        if role == 'Student':
            Student.objects.create(
                user=user,
                major=request.POST.get('student[major]', '').strip(),
                graduation_year=request.POST.get('student[graduation_year]', '').strip() or None,
            )
        else:
            Alumnus.objects.create(
                user=user,
                employer=request.POST.get('alumnus[employer]', '').strip(),
                job_title=request.POST.get('alumnus[job_title]', '').strip(),
                mentoring_interest=request.POST.get('alumnus[mentoring_interest]', '').strip(),
            )

        # 4) Log them in via session
        request.session['user_id'] = user.user_id

        # 5) Redirect to profile creation
        #    Make sure your URLconf names this "core:create_profile"
        return redirect('core:create_profile', user.user_id)


# class SignUpView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'core/signup.html'

#     def get(self, request):
#         return Response({}, template_name=self.template_name)

#     def post(self, request):
#         email = request.data.get('email')
#         password = request.data.get('password_hash')
#         name = request.data.get('name')
#         role = request.data.get('role')

#         # Validation
#         if not all([email, password, name, role]):
#             error = {"error": "All fields are required."}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_400_BAD_REQUEST)

#         if role not in ['Student', 'Alumnus']:
#             error = {"error": "Invalid role. Must be 'Student' or 'Alumnus'."}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_400_BAD_REQUEST)

#         # Check if user already exists
#         if User.objects.filter(email=email).exists():
#             error = {"error": "User with this email already exists."}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Create user
#             user = User.objects.create(
#                 name=name,
#                 email=email,
#                 password_hash=make_password(password),  # Hash the password
#                 role=role
#             )

#             # Create role-specific record
#             if role == 'Student':
#                 major = request.data.get('student[major]', '')
#                 graduation_year = request.data.get('student[graduation_year]', 2024)
#                 Student.objects.create(user=user, major=major, graduation_year=graduation_year)
#             else:
#                 employer = request.data.get('alumnus[employer]', '')
#                 job_title = request.data.get('alumnus[job_title]', '')
#                 mentoring_interest = request.data.get('alumnus[mentoring_interest]', False)
#                 Alumnus.objects.create(
#                     user=user,
#                     employer=employer,
#                     job_title=job_title,
#                     mentoring_interest=mentoring_interest
#                 )

#             # Auto sign-in the user
#             request.session['user_id'] = user.user_id

#             # For HTML responses, redirect to profile creation
#             if request.accepted_renderer.format == 'html':
#                 return redirect('core:create_profile', user.user_id)

#             # For API (JSON) responses, return redirect URL in payload
#             redirect_url = reverse('core:create_profile', args=[user.user_id])
#             return Response({
#                 "message": "User created successfully",
#                 "user_id": user.user_id,
#                 "redirect_url": redirect_url
#             }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             error = {"error": f"Error creating user: {str(e)}"}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class SignUpView(APIView):
#     renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
#     template_name = 'core/signup.html'
    
#     def get(self, request):
#         return Response({}, template_name=self.template_name)
    
#     def post(self, request):
#         email = request.data.get('email')
#         password = request.data.get('password_hash')
#         name = request.data.get('name')
#         role = request.data.get('role')
        
#         # Validation
#         if not all([email, password, name, role]):
#             error = {"error": "All fields are required."}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_400_BAD_REQUEST)

#         if role not in ['Student', 'Alumnus']:
#             error = {"error": "Invalid role. Must be 'Student' or 'Alumnus'."}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_400_BAD_REQUEST)

#         # Check if user already exists
#         if User.objects.filter(email=email).exists():
#             error = {"error": "User with this email already exists."}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Create user
#             user = User.objects.create(
#                 name=name,
#                 email=email,
#                 password_hash=make_password(password),  # Hash the password
#                 role=role
#             )

#             # Create role-specific record
#             if role == 'Student':
#                 # You might want to get these from the form
#                 major = request.data.get('student[major]', '')
#                 graduation_year = request.data.get('student[graduation_year]', 2024)
#                 Student.objects.create(user=user, major=major, graduation_year=graduation_year)
#             else:  # Alumnus
#                 employer = request.data.get('alumnus[employer]', '')
#                 job_title = request.data.get('alumnus[job_title]', '')
#                 mentoring_interest = request.data.get('alumnus[mentoring_interest]', False)
#                 Alumnus.objects.create(user=user, employer=employer, job_title=job_title, mentoring_interest=mentoring_interest)

#             # Auto sign-in the user
#             request.session['user_id'] = user.user_id
            
#             # Redirect to create profile
#             # redirect_url = f'/api/profile/create/{user.user_id}/'
#             redirect_url = reverse('core:create_profile', args=[user.user_id])
#         return redirect(redirect_url)
            
#             # For HTML responses, use HttpResponseRedirect to ensure proper redirection
#             if request.accepted_renderer.format == 'html':
#                 from django.shortcuts import redirect
#                 return redirect(redirect_url)
            
#             return Response({
#                 "message": "User created successfully", 
#                 "user_id": user.user_id,
#                 "redirect_url": redirect_url
#             }, status=status.HTTP_201_CREATED)
            
#         except Exception as e:
#             error = {"error": f"Error creating user: {str(e)}"}
#             if request.accepted_renderer.format == 'html':
#                 return Response({'errors': error}, template_name=self.template_name)
#             return Response(error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class CreateProfileView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/create_profile.html'
    
    def get(self, request, user_id):
        # Check if user exists
        try:
            user = User.objects.get(pk=user_id)
            # Check if profile already exists
            if Profile.objects.filter(user=user).exists():
                if request.accepted_renderer.format == 'html':
                    from django.shortcuts import redirect
                    return redirect(f'/api/profile/{user_id}/')
                return Response({"error": "Profile already exists"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Be more explicit about including the user object
            user_data = UserSerializer(user).data
            # Make sure user_id is included in context
            return Response({
                'user': user_data,
                'user_id': user_id  # Include user_id separately for safety
            }, template_name=self.template_name)
        except User.DoesNotExist:
            if request.accepted_renderer.format == 'html':
                return Response({'errors': {'error': 'User not found'}}, template_name=self.template_name)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
            
            # Check if profile already exists first
            existing_profile = Profile.objects.filter(user=user).first()
            if existing_profile:
                if request.accepted_renderer.format == 'html':
                    from django.shortcuts import redirect
                    return redirect(f'/api/profile/{user_id}/')
                return Response({"error": "Profile already exists", "profile_id": existing_profile.profile_id}, 
                               status=status.HTTP_400_BAD_REQUEST)
            
            # Create profile data
            profile_data = {
                'user': user_id,
                'bio': request.data.get('bio', ''),
                'skills': request.data.get('skills', []),
                'education': request.data.get('education', '')
            }
            
            serializer = ProfileSerializer(data=profile_data)
            if serializer.is_valid():
                try:
                    profile = serializer.save()
                    
                    if request.accepted_renderer.format == 'html':
                        from django.shortcuts import redirect
                        return redirect(f'/api/profile/{user_id}/')
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except IntegrityError:
                    # Handle the case where a profile was created concurrently
                    existing_profile = Profile.objects.filter(user=user).first()
                    if existing_profile:
                        if request.accepted_renderer.format == 'html':
                            from django.shortcuts import redirect
                            return redirect(f'/api/profile/{user_id}/')
                        return Response({"error": "Profile already exists", "profile_id": existing_profile.profile_id}, 
                                       status=status.HTTP_400_BAD_REQUEST)
            else:
                if request.accepted_renderer.format == 'html':
                    return Response({
                        'errors': serializer.errors,
                        'user': UserSerializer(user).data
                    }, template_name=self.template_name)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except User.DoesNotExist:
            if request.accepted_renderer.format == 'html':
                return Response({'errors': {'error': 'User not found'}}, template_name=self.template_name)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class UpdateProfileView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/update_profile.html'
    
    def get(self, request, profile_id):
        try:
            profile = Profile.objects.get(pk=profile_id)
            return Response({
                'profile': ProfileSerializer(profile).data,
                'user': UserSerializer(profile.user).data
            }, template_name=self.template_name)
        except Profile.DoesNotExist:
            if request.accepted_renderer.format == 'html':
                return Response({'errors': {'error': 'Profile not found'}}, template_name=self.template_name)
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, profile_id):
        try:
            profile = Profile.objects.get(pk=profile_id)
            serializer = ProfileSerializer(profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                if request.accepted_renderer.format == 'html':
                    return Response({
                        'success': True,
                        'profile': ProfileSerializer(profile).data,
                        'user': UserSerializer(profile.user).data,
                        'redirect': True,
                        'redirect_url': f'/api/profile/{profile.user.user_id}/'
                    }, template_name=self.template_name)
                return Response(serializer.data)
            else:
                if request.accepted_renderer.format == 'html':
                    return Response({
                        'errors': serializer.errors,
                        'profile': ProfileSerializer(profile).data,
                        'user': UserSerializer(profile.user).data
                    }, template_name=self.template_name)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        except Profile.DoesNotExist:
            if request.accepted_renderer.format == 'html':
                return Response({'errors': {'error': 'Profile not found'}}, template_name=self.template_name)
            return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, profile_id):
        # Handle PUT requests submitted via POST with _method=PUT
        if request.data.get('_method') == 'PUT':
            return self.put(request, profile_id)
        
        # Regular POST handling if needed
        return Response({"error": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


class GetProfileView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    template_name = 'core/profile.html'
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
            try:
                profile = Profile.objects.get(user=user)
                
                # Get additional user data based on role
                role_data = {}
                if user.role == 'Student':
                    try:
                        student = Student.objects.get(user=user)
                        role_data = StudentSerializer(student).data
                    except Student.DoesNotExist:
                        pass
                elif user.role == 'Alumnus':
                    try:
                        alumnus = Alumnus.objects.get(user=user)
                        role_data = AlumnusSerializer(alumnus).data
                    except Alumnus.DoesNotExist:
                        pass
                
                # Get the current logged-in user
                current_user_id = request.session.get('user_id')
                is_connected = False
                connection_pending = False
                
                # Only check connection status if the current user is viewing someone else's profile
                # and the current user is authenticated
                if current_user_id and str(current_user_id) != str(user_id):
                    # Check if they are already connected
                    try:
                        current_user = User.objects.get(pk=current_user_id)
                        is_connected = (
                            Connection.objects.filter(user1=current_user, user2=user).exists() or
                            Connection.objects.filter(user1=user, user2=current_user).exists()
                        )
                        
                        # Check if there's a pending connection request
                        if not is_connected:
                            connection_pending = (
                                ConnectionRequest.objects.filter(
                                    from_user=current_user, 
                                    to_user=user, 
                                    status='Pending'
                                ).exists()
                            )
                    except User.DoesNotExist:
                        current_user_id = None
                
                # Make sure we have a valid current_user object for the template
                current_user = None
                if current_user_id:
                    try:
                        current_user = User.objects.get(pk=current_user_id)
                    except User.DoesNotExist:
                        current_user_id = None
                
                # context = {
                #     'user': current_user,
                #     'profile': ProfileSerializer(profile).data,
                #     'role_data': role_data,
                #     'is_connected': is_connected,
                #     'connection_pending': connection_pending
                # }
                context = {
                    'user': current_user,
                    'profile': profile,  # Pass actual Profile model
                    'role_data': role_data,
                    'is_connected': is_connected,
                    'connection_pending': connection_pending
                }
                                
                # Pass the user_id even if we couldn't get the user object
                if current_user_id and not current_user:
                    context['user'] = {'user_id': current_user_id}
                
                return Response(context, template_name=self.template_name)
                
            except Profile.DoesNotExist:
                # If profile doesn't exist, redirect to create profile
                if request.accepted_renderer.format == 'html':
                    from django.shortcuts import redirect
                    return redirect(f'/api/profile/create/{user_id}/')
                return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
                
        except User.DoesNotExist:
            if request.accepted_renderer.format == 'html':
                return Response({'errors': {'error': 'User not found'}}, template_name=self.template_name)
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)