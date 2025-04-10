from django.shortcuts import render
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from rest_framework import viewsets
from .models import File, Category, FileApproval, OCRData, FileActivityLog, Backup
from .serializers import (FileSerializer,CategorySerializer,FileApprovalSerializer,  OCRDataSerializer, FileActivityLogSerializer)
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .permissions import *
import logging

logger = logging.getLogger(__name__)

from datetime import timedelta
from django.utils import timezone
from celery import shared_task
from django.utils.timezone import now
# import random
from django.core.mail import send_mail
from django.conf import settings
from users.models import User

import cv2
import numpy as np

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user  
        file_instance = serializer.save(uploaded_by=user)  
        
         # Log file upload activity
        FileActivityLog.objects.create(
            file=file_instance,
            user=user,
            action='upload',
            notes='File uploaded via API'
        )

        # ✅ Create Backup
        Backup.objects.create(
            file=file_instance.file,
            name=file_instance.name,
            category=file_instance.category,
            file_type=file_instance.file_type,
            is_approved=file_instance.is_approved,
            uploaded_by=user
        )
       # 🔥 Auto-create a FileApproval and send mail manually
        approver = User.objects.filter(is_staff=True).exclude(id=user.id).first()
        if approver:
            approval = FileApproval.objects.create(
                file=file_instance,
                approver=approver,
                status='pending'
            )
        
        # ✅ Manually send the email (since perform_create of FileApprovalViewSet isn't triggered)
        if approver.email:
            send_mail(
                subject='New File Pending Approval',
                message=f'Dear {approver.get_full_name()},\n\n'
                        f'A file "{file_instance.name}" has been submitted and requires your approval.\n\n'
                        f'Please log in to the system to review it.\n\nThank you.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[approver.email],
                fail_silently=True
            )

        # ✅ Schedule escalation
        escalate_pending_approval.apply_async((approval.id,), eta=now() + timedelta(hours=24))
        # ✅ Perform OCR on images and PDFs with enhancement
        file_path = file_instance.file.path
        extracted_text = ""

        try:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                image = cv2.imread(file_path)
                image = self.preprocess_image(image)
                extracted_text = pytesseract.image_to_string(image)

            elif file_path.lower().endswith('.pdf'):
                images = convert_from_path(file_path)
                for image in images:
                    image = np.array(image)
                    image = self.preprocess_image(image)
                    extracted_text += pytesseract.image_to_string(image) + "\n"

            if extracted_text:
                OCRData.objects.create(file=file_instance, extracted_text=extracted_text)
                logger.info(f"OCRData successfully created for file: {file_instance.name}")
            else:
                logger.warning(f"OCRData extraction failed: No text found in {file_instance.name}")

        except Exception as e:
            logger.error(f"OCR Extraction Error: {e}")

    def preprocess_image(self, image):
        """Enhances the image before OCR."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

      
    
    @action(detail=True, methods=['POST'], permission_classes=[IsOwnerOrAdmin])
    def restore(self, request, pk=None):
        """Restores a file from backup"""
        try:
            backup_instance = Backup.objects.get(pk=pk)

            # Prevent restoring if the file already exists
            if File.objects.filter(file=backup_instance.file, uploaded_by=backup_instance.uploaded_by).exists():
                return Response(
                    {"error": "This file has already been restored."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Restore the file
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

    @action(detail=True, methods=['GET'], permission_classes=[IsOwnerOrAdmin])
    def get_ocr_text(self, request, pk=None):
        """API endpoint to retrieve OCR text for a file"""
        try:
            ocr_data = OCRData.objects.get(file_id=pk)
            return Response({"file_id": pk, "extracted_text": ocr_data.extracted_text})
        except OCRData.DoesNotExist:
            return Response({"error": "No OCR data found for this file"}, status=status.HTTP_404_NOT_FOUND)


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
            
        # ✅ Notify uploader if file is approved
        if approval.status == 'approved' and approval.file.uploaded_by.email:
            send_mail(
                subject='Your File Has Been Approved',
                message=f'Dear {approval.file.uploaded_by.get_full_name()},\n\n'
                        f'Your file "{approval.file.name}" has been approved by {approval.approver.get_full_name()}.\n\n'
                        f'Thank you for using our service!',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[approval.file.uploaded_by.email],
                fail_silently=True
            )
            
        # ✅ Notify uploader if file is rejected
        if approval.status == 'rejected' and approval.file.uploaded_by.email:
            send_mail(
                subject='Your File Has Been Rejected',
                message=f'Dear,\n\n'
                        f'We regret to inform you that your file "{approval.file.name}" has been rejected.\n\n'
                        f'Please review the feedback from the approver and make necessary changes.\n\n'
                        f'Thank you for using our service!',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[approval.file.uploaded_by.email],
                fail_silently=True
            )

        
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
                recipient_list=[settings.EMAIL_HOST_USER],  # replace with actual higher authority
                fail_silently=True
            )
    except FileApproval.DoesNotExist:
        pass
    

# class OCRDataViewSet(viewsets.ModelViewSet):
#     queryset = OCRData.objects.all()
#     serializer_class = OCRDataSerializer

class FileActivityLogViewSet(viewsets.ModelViewSet):
    queryset = FileActivityLog.objects.all()
    serializer_class = FileActivityLogSerializer
