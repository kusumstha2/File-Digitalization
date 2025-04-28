from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Category,File, FileApproval, OCRData, FileActivityLog, Backup,AccessRequest

admin.site.register(Category)
admin.site.register(File)
admin.site.register(FileApproval)
admin.site.register(OCRData)
admin.site.register(FileActivityLog)
admin.site.register(Backup)

@admin.register(AccessRequest)
class AccessRequestAdmin(admin.ModelAdmin):
    list_display = ('file', 'requester', 'is_approved', 'reviewed_by', 'created_at', 'reviewed_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('file__name', 'requester__name')
