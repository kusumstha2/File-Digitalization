from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (FileViewSet, CategoryViewSet, FileApprovalViewSet,
                    OCRDataViewSet, FileActivityLogViewSet)

router = DefaultRouter()
router.register('files', FileViewSet)
router.register('categories', CategoryViewSet)
router.register('approvals', FileApprovalViewSet)
router.register('ocrdata', OCRDataViewSet)
router.register('fileactivity', FileActivityLogViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
