from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import File, Category, FileApproval, OCRData, FileActivityLog
from .serializers import (FileSerializer,CategorySerializer,FileApprovalSerializer,  OCRDataSerializer, FileActivityLogSerializer)

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer



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
