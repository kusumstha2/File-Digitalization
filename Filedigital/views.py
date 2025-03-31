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

import cv2
import numpy as np

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user  
        file_instance = serializer.save(uploaded_by=user)  

        # ✅ Create Backup
        Backup.objects.create(
            file=file_instance.file,
            name=file_instance.name,
            category=file_instance.category,
            file_type=file_instance.file_type,
            is_approved=file_instance.is_approved,
            uploaded_by=user
        )

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



# class OCRDataViewSet(viewsets.ModelViewSet):
#     queryset = OCRData.objects.all()
#     serializer_class = OCRDataSerializer

class FileActivityLogViewSet(viewsets.ModelViewSet):
    queryset = FileActivityLog.objects.all()
    serializer_class = FileActivityLogSerializer


