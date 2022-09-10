from os import stat
from urllib import request
from django.shortcuts import render
from django.http import JsonResponse
from rest_framework import generics, status
from .serializers import RoomSerializer, CreateRoomSerializer
from .models import Room
from rest_framework.views import APIView
from rest_framework.response import Response

class RoomView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
    
class GetRoom(APIView):
    lookup_url_kwrag = 'code'
    
    def get(self, request, format=None):
        code = request.query_params.get(self.lookup_url_kwrag)
        if code != None:
            room = Room.objects.filter(code=code)
            if len(room) > 0:
                data = RoomSerializer(room[0]).data
                data['is_host'] = self.request.session.session_key == room[0].host
                return Response(data, status=status.HTTP_200_OK)
            return Response({'Room Not Found': 'Invalid Room Code'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'Bad Request': 'Code parameter not found in request'}, status=status.HTTP_400_BAD_REQUEST)
        
                
class JoinRoom(APIView):
    lookup_url_kwarg = 'code'
    
    def post(self,request,format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        
        code = request.data.get(self.lookup_url_kwarg)
        if code != None:
            room_result = Room.objects.filter(code=code)
            if len(room_result) > 0:
                self.request.session['room_code'] = code
                return Response({'message': 'Joined!'}, status=status.HTTP_200_OK)
            return Response({'bad request':'invalid code'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'bad request':'invalid data could not find code key'}, status=status.HTTP_400_BAD_REQUEST)


class CreateRoomView(APIView):
    
    def post(self, request, format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        
        serializer = CreateRoomSerializer(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.data.get('guest_can_pause')
            votes_to_skip = serializer.data.get('votes_to_skip')
            host = self.request.session.session_key
            queryset = Room.objects.filter(host=host)
            if queryset.exists():
                room = queryset[0]
                room.guest_can_pause = guest_can_pause
                room.votes_to_skip = votes_to_skip
                room.save(update_fields=['guest_can_pause', 'votes_to_skip'])
                self.request.sesion['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            else :
                room = Room(
                    host=host,
                    guest_can_pause=guest_can_pause,
                    votes_to_skip=votes_to_skip
                )
                room.save()
                self.request.sesion['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            
class UserInRoom(APIView):
    def get(self, request, format=None):
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        data = {
            'code': self.request.session.get('room_code')
        }
        return JsonResponse(data,status=status.HTTP_200_OK)
    
class LeaveRoom(APIView):
    def post(self, request, format=None):
        if 'room_code' in self.request.session:
            self.request.session.pop('room_code')
            host_id = self.request.session.session_key
            room_results = Room.objects.filter(host=host_id)
            if len(room_results) > 0:
                room = room_results[0]
                room.delete()
        return Response({'message' : 'Success'}, status=status.HTTP_200_OK)
    