from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import File, Category, FileApproval, OCRData, FileActivityLog, Backup
from .serializers import (FileSerializer,CategorySerializer,FileApprovalSerializer,  OCRDataSerializer, FileActivityLogSerializer)
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .permissions import *


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsOwnerOrAdmin]
    def perform_create(self, serializer):
        user = self.request.user  # Get the authenticated user
        file_instance = serializer.save(uploaded_by=user)  # Save the File instance

        # Also create a Backup instance
        Backup.objects.create(
            file=file_instance.file,  # Copy file field
            name=file_instance.name,
            category=file_instance.category,
            file_type=file_instance.file_type,
            is_approved=file_instance.is_approved,
            uploaded_by=user  # Set uploaded_by to the same user
        )
    @action(detail=True, methods=['POST'], permission_classes=[IsOwnerOrAdmin])
    def restore(self, request, pk=None):
        try:
            # Fetch the backup entry based on file_id
            backup_instance = Backup.objects.get(pk=pk)
            
            #Explicitly check if the request user is either the owner or an admin

            if not (request.user.is_staff or backup_instance.uploaded_by == request.user):
                return Response(
                    {"error": "You do not have permission to restore this file."},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            # ✅ Prevent restoring if file already exists
            if File.objects.filter(file=backup_instance.file, uploaded_by=backup_instance.uploaded_by).exists():
                return Response(
                    {"error": "This file has already been restored."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            # Restore the file by recreating a File instance
            restored_file = File.objects.create(
                file=backup_instance.file,
                name=backup_instance.name,
                added_date=backup_instance.added_date,
                category=backup_instance.category,
                file_type=backup_instance.file_type,
                is_approved=backup_instance.is_approved,
                uploaded_by=backup_instance.uploaded_by
            )

            return Response(
                {"message": "File restored successfully", "file_id": restored_file.id},
                status=status.HTTP_201_CREATED
            )

        except Backup.DoesNotExist:
            return Response({"error": "Backup file not found"}, status=status.HTTP_404_NOT_FOUND)



class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class FileApprovalViewSet(viewsets.ModelViewSet):
    queryset = FileApproval.objects.all()
    serializer_class = FileApprovalSerializer



class OCRDataViewSet(viewsets.ModelViewSet):
    queryset = OCRData.objects.all()
    serializer_class = OCRDataSerializer

class FileActivityLogViewSet(viewsets.ModelViewSet):
    queryset = FileActivityLog.objects.all()
    serializer_class = FileActivityLogSerializer
