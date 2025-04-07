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

from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.utils.timezone import now
# import random
from django.core.mail import send_mail
from django.conf import settings
from users.models import User


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsOwnerOrAdmin]
    def perform_create(self, serializer):
        user = self.request.user  # Get the authenticated user
        file_instance = serializer.save(uploaded_by=user)  # Save the File instance
        
         # Log file upload activity
        FileActivityLog.objects.create(
            file=file_instance,
            user=user,
            action='upload',
            notes='File uploaded via API'
        )

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
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        approval = serializer.save()

        # Update File's is_approved based on status
        if approval.status == 'approved':
            approval.file.is_approved = True
        else:
            approval.file.is_approved = False
        approval.file.save()

        # Set decision_date if status is not pending
        if approval.status != 'pending':
            approval.decision_date = now()
            approval.save()

        # Log activity
        FileActivityLog.objects.create(
            file=approval.file,
            user=approval.approver,
            action=approval.status,
            notes=approval.notes
        )
        
        # # ✅ Notify approver via email when approval is pending
        # if approval.status == 'pending' and approval.approver.email:
        #     send_mail(
        #         subject='New File Pending Approval',
        #         message=f'Dear {approval.approver.get_full_name()},\n\n'
        #                 f'A file "{approval.file.name}" has been submitted and requires your approval.\n\n'
        #                 f'Please log in to the system to review it.\n\nThank you.',
        #         from_email=settings.EMAIL_HOST_USER,
        #         recipient_list=[approval.approver.email],
        #         fail_silently=True
        #     )
        
        # Escalation setup after 24 hours
        if approval.status == 'pending':
            escalate_pending_approval.apply_async((approval.id,), eta=now() + timedelta(hours=24))
        
@shared_task
def escalate_pending_approval(approval_id):
    from .models import FileApproval
    try:
        approval = FileApproval.objects.get(id=approval_id)
        if approval.status == 'pending':
            # Escalate logic (e.g., notify admin or higher authority)
            # Here we just print/log; you can notify via email, update approver, etc.
            print(f"Approval {approval_id} is still pending. Escalating...")

            # Optional: send email to admin
            send_mail(
                subject='Approval Escalation Alert',
                message=f'File "{approval.file.name}" is still pending approval after 24 hours.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=['krijalsuwal67@gmail.com'],  # replace with actual higher authority
                fail_silently=True
            )
    except FileApproval.DoesNotExist:
        pass
    

class OCRDataViewSet(viewsets.ModelViewSet):
    queryset = OCRData.objects.all()
    serializer_class = OCRDataSerializer

class FileActivityLogViewSet(viewsets.ModelViewSet):
    queryset = FileActivityLog.objects.all()
    serializer_class = FileActivityLogSerializer
