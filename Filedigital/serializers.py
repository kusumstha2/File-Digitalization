from rest_framework import serializers
from .models import File, Category, FileApproval, OCRData, FileActivityLog,Notification

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        exclude = ['uploaded_by']



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class FileApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileApproval
        fields = '__all__'
        read_only_fields = ['request_date', 'decision_date']



class OCRDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRData
        fields = '__all__'

class FileActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileActivityLog
        fields = '__all__'

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'