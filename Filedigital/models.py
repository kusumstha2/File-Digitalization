from django.db import models
from users.models import *
# Create your models here.
from django.db import models
from django.conf import settings
class Category(models.Model):
    name = models.CharField(max_length=255, unique=True,default=1)

    def __str__(self):
        return self.name

import os
# models.py
import os

class File(models.Model):
    FILE_TYPES = [
        ('private', 'Private'),
        ('public', 'Public')
    ]

    file = models.FileField(upload_to='documents/', unique=True)
    name = models.CharField(max_length=255, unique=True)
    added_date = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE,null=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='private')
    is_approved = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='upload')

    def save(self, *args, **kwargs):
        if self.file:
            ext = os.path.splitext(self.file.name)[1].lower()

            if ext == '.pdf':
                category_name = "PDF"
            elif ext in ['.jpg', '.jpeg', '.png']:
                category_name = "Image"
            elif ext in ['.doc', '.docx']:
                category_name = "Word Document"
            elif ext in ['.xls', '.xlsx']:
                category_name = "Excel Sheet"
            elif ext in ['.ppt', '.pptx']:
                category_name = "PowerPoint Presentation"
            elif ext in ['.txt']:
                category_name = "Text File"
            elif ext in ['.zip', '.rar']:
                category_name = "Compressed File"
            else:
                category_name = "Other Files"

            # 🛠 Automatically create category if not exist
            category_obj, created = Category.objects.get_or_create(name=category_name)

            self.category = category_obj

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AccessRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('denied', 'Denied'),
    ]

    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='access')  
    file = models.ForeignKey(File, on_delete=models.CASCADE)  
    is_approved = models.BooleanField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"Request by {self.requester.name} requests access to {self.file.name} "

class Backup(models.Model):
    FILE_TYPES = [
        ('private', 'Private'),
        ('public', 'Public')
    ]   

    file = models.FileField(upload_to='backup_documents/')
    name = models.CharField(max_length=255)
    added_date = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, default='private')
    is_approved = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name='backup_upload')

    def __str__(self):
        return self.name

class FileApproval(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ]

    file = models.ForeignKey(File, on_delete=models.CASCADE)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="approver")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    decision_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.file.name} - {self.status} - {self.approver.id}"




class FileActivityLog(models.Model):
    ACTION_CHOICES = [
        ('upload', 'Upload'),
        ('approve', 'Approve'),
        ('reject', 'Reject'),
        ('download', 'Download'),
        ('share', 'Share'),
        ('comment', 'Comment')
    ]

    file = models.ForeignKey(File, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.file.name}"

class OCRData(models.Model):
    file = models.OneToOneField(File, on_delete=models.CASCADE)
    extracted_text = models.TextField()

    def __str__(self):
        return f"OCR Data for {self.file.name}"


class Notification(models.Model):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=True)

    def __str__(self):
        return f"Notification for {self.user_id.username} - {self.message[:50]}..."  
