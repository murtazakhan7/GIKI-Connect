from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User, Student, Alumnus, Profile
from .serializers import (
    UserSerializer, StudentSerializer, AlumnusSerializer, ProfileSerializer
)
from django.contrib.auth.hashers import make_password


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
                if student_serializer.is_valid():
                    student_serializer.save()
                else:
                    user.delete()
                    return Response(student_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            elif role == 'Alumnus':
                alumnus_data = request.data.get('alumnus', {})
                alumnus_data['user'] = user.user_id
                alumnus_serializer = AlumnusSerializer(data=alumnus_data)
                if alumnus_serializer.is_valid():
                    alumnus_serializer.save()
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
            data['user'] = user.user_id
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
