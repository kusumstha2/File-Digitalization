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

import threading
import time

logger = logging.getLogger(__name__)

from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now

from django.core.mail import send_mail
from django.conf import settings
from users.models import User
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.cache import cache_page
from django.core.cache import cache

import cv2
import numpy as np

from .models import File, Backup
from .utils import encrypt_file
import os
from .utils import decrypt_file
from django.core.files.base import ContentFile
from rest_framework.permissions import DjangoModelPermissions

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.db.models import Count
# from .models import FileActivityLog



CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer 
    permission_classes = [DjangoModelPermissions]

    def perform_create(self, serializer):
        user = self.request.user  
        file_instance = serializer.save(uploaded_by=user)
        
        # Read original file content
        with open(file_instance.file.path, 'rb') as f:
            raw_data = f.read()
        
        # Encrypt the content
        encrypted_data = encrypt_file(raw_data)
        
        # Set backup path
        backup_filename = f"{file_instance.name}.enc"
        backup_path = os.path.join(settings.MEDIA_ROOT, 'backup_documents', backup_filename)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        # Save encrypted file
        with open(backup_path, 'wb') as f:
            f.write(encrypted_data)
        
         # Log file upload activity
        FileActivityLog.objects.create(
            file=file_instance,
            user=user,
            action='upload',
            notes='File uploaded via API'
        )

        # ✅ Create Backup
        Backup.objects.create(
            file=f"backup_documents/{backup_filename}",
            name=file_instance.name,
            category=file_instance.category,
            file_type=file_instance.file_type,
            is_approved=file_instance.is_approved,
            uploaded_by=user
        )
       # 🔥 Auto-create a FileApproval and send mail manually
        approver = User.objects.filter(is_staff=True).exclude(id=user.id).first()
        approval = None
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

        # Start background thread for escalation
        if approval:
            threading.Thread(target=escalate_pending_approval_thread, args=(approval.id,), daemon=True).start()
            
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

      
    
    # @action(detail=True, methods=['POST'], permission_classes=[IsOwnerOrAdmin])
    # def restore(self, request, pk=None):
    #     """Restores a file from backup"""
    #     try:
    #         backup_instance = Backup.objects.get(pk=pk)

    #         # Prevent restoring if the file already exists
    #         if File.objects.filter(file=backup_instance.file, uploaded_by=backup_instance.uploaded_by).exists():
    #             return Response(
    #                 {"error": "This file has already been restored."},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )

    #         # Restore the file
    #         restored_file = File.objects.create(
    #             file=backup_instance.file,
    #             name=backup_instance.name,
    #             added_date=backup_instance.added_date,
    #             category=backup_instance.category,
    #             file_type=backup_instance.file_type,
    #             is_approved=backup_instance.is_approved,
    #             uploaded_by=backup_instance.uploaded_by
    #         )

    #         return Response(
    #             {"message": "File restored successfully", "file_id": restored_file.id},
    #             status=status.HTTP_201_CREATED
    #         )

    #     except Backup.DoesNotExist:
    #         return Response({"error": "Backup file not found"}, status=status.HTTP_404_NOT_FOUND)
    
    @action(methods=["post"], detail=False)
    def restore(self, request):
        backup_id = request.data.get("backup_id")

        if not backup_id:
            return Response({"error": "Backup ID is required"}, status=400)

        try:
            backup_instance = Backup.objects.get(id=backup_id)
        except Backup.DoesNotExist:
            return Response({"error": "Backup not found"}, status=404)

        backup_path = os.path.join(settings.MEDIA_ROOT, backup_instance.file.name)

        # Read and decrypt file
        try:
            with open(backup_path, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = decrypt_file(encrypted_data)
        except Exception as e:
            return Response({"error": f"Failed to decrypt file: {str(e)}"}, status=500)

        # Create new file
        content_file = ContentFile(decrypted_data, name=backup_instance.name)

        restored_file = File.objects.create(
            file=content_file,
            name=backup_instance.name,
            category=backup_instance.category,
            file_type=backup_instance.file_type,
            is_approved=backup_instance.is_approved,
            uploaded_by=backup_instance.uploaded_by
        )

        serializer = FileSerializer(restored_file)
        return Response(serializer.data, status=201)

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
    permission_classes = [DjangoModelPermissions]


class FileApprovalViewSet(viewsets.ModelViewSet):
    queryset = FileApproval.objects.all()
    serializer_class = FileApprovalSerializer
    permission_classes = [DjangoModelPermissions]
    
    
# def get_renderers(self):
#     user = self.request.user
#     if user.groups.filter(name='Viewer').exists():
#         return [JSONRenderer()]  # Must return at least one renderer to avoid crash
#     return [JSONRenderer(), BrowsableAPIRenderer()]

#     def dispatch(self, request, *args, **kwargs):
#         if request.user.groups.filter(name='Viewer').exists():
#             return Response({'detail': 'You do not have permission to access this endpoint.'},
#                             status=status.HTTP_403_FORBIDDEN)
#         return super().dispatch(request, *args, **kwargs)
    
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
            threading.Thread(target=escalate_pending_approval_thread, args=(approval.id,), daemon=True).start()
        
def escalate_pending_approval_thread(approval_id):
    """Runs in background to check after 24h and escalate if still pending"""
    logger.info(f"🚀 Escalation thread started for approval ID {approval_id}")
    time.sleep(60*60*24)  # 24 hours
    from .models import FileApproval
    try:
        approval = FileApproval.objects.get(id=approval_id)
        logger.info(f"📌 Approval status after wait: {approval.status}")

        if approval.status == 'pending':
            try:
                logger.info(f"📧 Escalation email will be sent to: {settings.EMAIL_HOST_USER}") 
                
                send_mail(
                    subject='Approval Escalation Alert',
                    message=f'File "{approval.file.name}" is still pending approval after 24 hours.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[settings.EMAIL_HOST_USER],  # Replace as needed
                    fail_silently=False
                )
                logger.info(f"Escalation email sent for file {approval.file.name}")
            except Exception as e:
                logger.error(f"Failed to send escalation email: {e}")
                
    except FileApproval.DoesNotExist:
        logger.error(f"❌ Approval with ID {approval_id} does not exist.")
    


class FileActivityLogViewSet(viewsets.ModelViewSet):
    queryset = FileActivityLog.objects.all()
    serializer_class = FileActivityLogSerializer


# 🗓 Weekly Report Scheduler (Auto-run every 7 days)
def generate_report():
    now = datetime.now()
    last_week = now - timedelta(days=7)

    logs = FileActivityLog.objects.filter(timestamp__range=(last_week, now))

    print(f"[{now}] Weekly report generated with {logs.count()} logs")

    # You can add logic here to:
    # - Save to PDF
    # - Send email to admin
    # - Save to model etc.

    # Schedule next report after 7 days (604800 seconds)
    threading.Timer(604800, generate_report).start()
    


@staff_member_required
def report_data(request):
    report_type = request.GET.get('type')

    if report_type == 'action_counts':
        data = FileActivityLog.objects.values('action').annotate(count=Count('id'))

    elif report_type == 'user_activity':
        data = FileActivityLog.objects.values('user__email').annotate(count=Count('id')).order_by('-count')

    elif report_type == 'file_popularity':
        data = FileActivityLog.objects.exclude(file_isnull=True).values('file_name').annotate(count=Count('id')).order_by('-count')

    elif report_type == 'logins':
        data = FileActivityLog.objects.filter(action='login').values('user__email').annotate(count=Count('id')).order_by('-count')
    
    elif report_type == 'logouts':
        data = FileActivityLog.objects.filter(action='logout').values('user__email').annotate(count=Count('id')).order_by('-count')
        
    elif report_type == 'logouts':
        data = FileActivityLog.objects.filter(action='logout').values('user__email').annotate(count=Count('id')).order_by('-count')

    else:
        return JsonResponse({'error': 'Invalid report type'}, status=400)

    return JsonResponse(
        {'report_type': report_type, 'results': list(data)},
        status=200,
        json_dumps_params={'indent': 2}
    )

