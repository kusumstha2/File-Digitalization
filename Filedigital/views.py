from django.shortcuts import render
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from django.contrib.postgres.search import SearchVector, SearchQuery
from rest_framework import viewsets,status
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
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
import json
import cv2
import numpy as np
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from rest_framework.response import Response
def get_or_set_cache(cache_key, queryset, serializer_class, timeout=60*15, force_refresh=False):
    """
    Fetch data from cache or set cache if not available.
    If data is not found in cache, it is fetched from the database
    and cached for subsequent requests.
    """
    if force_refresh:
        cache.delete(cache_key)  # Force cache deletion before fetching from the DB

    data = cache.get(cache_key)

    if data is None:
        print(f"Fetching {cache_key} from Database...")
        serialized_data = serializer_class(queryset, many=True).data
        cache.set(cache_key, json.dumps(serialized_data), timeout)
        print(f"Cache set for {cache_key}")
        return serialized_data
    else:
        print(f"Fetching {cache_key} from Cache...")
        return json.loads(data)

def invalidate_cache(cache_key):
    """
    Invalidate a specific cache key.
    """
    cache.delete(cache_key)
    print(f"Cache invalidated for key: {cache_key}")


    
class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request):
        cache_key = 'file_list'

        # 1. Try to get data from cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            print(f"✅ Fetching '{cache_key}' from Cache...")
            return Response(json.loads(cached_data))

        # 2. If cache miss, get data from DB
        print(f"❌ '{cache_key}' not found in cache. Fetching from DB...")
        queryset = File.objects.all()
        serializer = FileSerializer(queryset, many=True)
        data = serializer.data

        # 3. Store data in cache for 15 minutes (or any desired time)
        cache.set(cache_key, json.dumps(data), timeout=60 * 15)
        print(f"📦 Stored '{cache_key}' in cache.")

        return Response(data)
    def retrieve(self, request, *args, **kwargs):
        cache_key = f"File{kwargs.get('pk')}"
        return Response(get_or_set_cache(cache_key, File.objects.filter(pk=kwargs.get('pk')), self.serializer_class))

    def perform_create(self, serializer):
        serializer.save()
        user = self.request.user  
        file_instance = serializer.save(uploaded_by=user)  
        invalidate_cache("all_files")

  
        
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
        escalate_pending_approval.apply_async((approval.id,), eta=now() + timedelta(minutes=1))
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

    def list(self, request, *args, **kwargs):
        cached_data = cache.get('category_list')
        if cached_data:
            print("✅ Serving from cache: category list")
            return Response(cached_data)

        print("❌ 'category_list' not found in cache. Fetching from DB...")
        response = super().list(request, *args, **kwargs)
        cache.set('category_list', response.data, timeout=60 * 15)
        print("📦 Stored 'category_list' in cache.")
        return response

class FileApprovalViewSet(viewsets.ModelViewSet):
    queryset = FileApproval.objects.all()
    serializer_class = FileApprovalSerializer

    def list(self, request, *args, **kwargs):
        cached_data = cache.get('file_approval_list')
        if cached_data:
            print("✅ Serving from cache: file approvals")
            return Response(cached_data)

        print("❌ 'file_approval_list' not found in cache. Fetching from DB...")
        response = super().list(request, *args, **kwargs)
        cache.set('file_approval_list', response.data, timeout=60 * 15)
        print("📦 Stored 'file_approval_list' in cache.")
        return response

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
            escalate_pending_approval.apply_async((approval.id,), eta=now() + timedelta(minutes=1))
        
# views.py

from .task import escalate_pending_approval


class FileActivityLogViewSet(viewsets.ModelViewSet):
    queryset = FileActivityLog.objects.all()
    serializer_class = FileActivityLogSerializer
    def list(self, request, *args, **kwargs):
            cache_key = 'activity_log_list'

            # Check if the data is cached
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                print("✅ Serving from cache: activity logs")
                return Response(json.loads(cached_data))

            # If not cached, get data from DB
            print("❌ Cache miss. Fetching activity logs from DB...")
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

            # Cache the serialized data for 15 minutes
            cache.set(cache_key, json.dumps(data), timeout=60 * 15)
            print("📦 Activity logs cached.")

            return Response(data)
        
    def retrieve(self, request, *args, **kwargs):
        cache_key = f"File{kwargs.get('pk')}"
        return Response(get_or_set_cache(cache_key, FileActivityLog.objects.filter(pk=kwargs.get('pk')), self.serializer_class))

    def perform_create(self, serializer):
        serializer.save()
 
        invalidate_cache("all_fileactivitylog")

  