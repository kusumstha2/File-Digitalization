from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Category,File, FileApproval, OCRData, FileActivityLog, Backup

admin.site.register(Category)
admin.site.register(File)
admin.site.register(FileApproval)
admin.site.register(OCRData)
admin.site.register(FileActivityLog)
admin.site.register(Backup)
