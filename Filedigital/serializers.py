from rest_framework import serializers
from .models import File, Category, FileApproval, OCRData, FileActivityLog

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'



class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class FileApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileApproval
        fields = '__all__'



class OCRDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRData
        fields = '__all__'

class FileActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileActivityLog
        fields = '__all__'
