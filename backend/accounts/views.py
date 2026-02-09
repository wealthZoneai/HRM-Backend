from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer, RegisterSerializer


# Home API (public)
@api_view(['GET'])
@permission_classes([AllowAny])
def home(request):
    return Response({"message": "Welcome to the API Demo!"})


# Signup API
@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({"message": "User created successfully!"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Login API
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key,"message": "user logged in successfully", "username": user.username})
    return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


# Logout API
@api_view(['POST'])
def logout(request):
    request.user.auth_token.delete()
    return Response({"message": "Logged out successfully!"})


# Protected Profile API
@api_view(['GET'])
def profile(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
