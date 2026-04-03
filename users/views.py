"""
Views for the users app.

Handles user listing, creation, detail, and authentication endpoints.
"""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from .models import UserProfile
from .permissions import IsAdminRole
from .serializers import UserSerializer, UserCreateSerializer, UserUpdateSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminRole])
def user_list(request):
    """
    List all users. Admin only.
    GET /api/users/
    """
    users = User.objects.select_related('profile').all().order_by('username')
    serializer = UserSerializer(users, many=True)
    return Response({'users': serializer.data, 'count': users.count()})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminRole])
def user_create(request):
    """
    Create a new user with a specified role. Admin only.
    POST /api/users/create/
    """
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {'message': 'User created successfully.', 'user': UserSerializer(user).data},
            status=status.HTTP_201_CREATED
        )
    return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def user_detail(request, user_id):
    """
    Retrieve, update, or delete a specific user.
    GET   /api/users/<id>/  — any authenticated user (own record), admin sees all
    PUT   /api/users/<id>/  — admin only
    DELETE /api/users/<id>/ — admin only
    """
    try:
        user = User.objects.select_related('profile').get(pk=user_id)
    except User.DoesNotExist:
        return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    profile = getattr(request.user, 'profile', None)
    is_admin = profile and profile.is_admin
    is_own_record = request.user.pk == user.pk

    if request.method == 'GET':
        if not is_admin and not is_own_record:
            return Response(
                {'error': 'You can only view your own profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return Response(UserSerializer(user).data)

    if not is_admin:
        return Response(
            {'error': 'Only admins can modify user records.'},
            status=status.HTTP_403_FORBIDDEN
        )

    if request.method == 'PUT':
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'User updated successfully.',
                'user': UserSerializer(user).data
            })
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        if user.pk == request.user.pk:
            return Response(
                {'error': 'You cannot delete your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        username = user.username
        user.delete()
        return Response({'message': f'User "{username}" deleted successfully.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Return the currently authenticated user's profile.
    GET /api/users/me/
    """
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Authenticate a user and create a session.
    POST /api/users/login/
    Body: { "username": "...", "password": "..." }
    """
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '')

    if not username or not password:
        return Response(
            {'error': 'Both username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response(
            {'error': 'Invalid credentials.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    login(request, user)
    return Response({
        'message': 'Login successful.',
        'user': UserSerializer(user).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Log out the current user and destroy their session.
    POST /api/users/logout/
    """
    logout(request)
    return Response({'message': 'Logged out successfully.'})
