from os import access
from urllib import request
from django.shortcuts import render, redirect
from rest_framework.views import APIView
from requests import Request, post
from rest_framework import status
from rest_framework.response import Response
from .util import is_spotify_authenticated, update_or_create_user_tokens
from decouple import config

# Create your views here.

class AuthURL(APIView):
    def get(self, request, format=None):
        scopes = 'user-read-playback-state user-modify-playback-state user-read-currently-playing'
        
        url = Request('GET', 'https://accounts.spotify.com/authorize', params={
            'scope' : scopes,
            'response_type' : 'code',
            'redirect_uri' : config('REDIRECT_URI'),
            'client_id' : config('CLIENT_ID'),
        }).prepare().url
        
        return Response({'url':url}, status=status.HTTP_200_OK)
        
def spotify_callback(request, format=None):
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    response = post('https://accounts.spotify.com/api/token', data={
        'code': code,
        'redirect_uri':config('REDIRECT_URI'),
        'grant_type': 'authorization_code',
        'client_id':config('CLIENT_ID'),
        'client_secret':config('CLIENT_SECRET'),
    }).json()
    
    access_token = response.get('access_token')
    token_type = response.get('token_type')
    refresh_token = response.get('refresh_token')
    expires_in = response.get('expires_in')
    error = response.get('error')
    
    if not request.session.exists(request.session.session_key):
        request.session.create()
    
    update_or_create_user_tokens(request.session.session_key, access_token, token_type, expires_in, refresh_token)
    
    return redirect('frontend:')

class IsAuthenticated(APIView):
    def get(self, requset, format=None):
        is_authenticated = is_spotify_authenticated(self.request.session.session_key)
        return Response({'status':is_authenticated}, status=status.HTTP_200_OK)