from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ReviewViewSet,
    ReviewReplyViewSet,
    ReviewReportViewSet,
    ReviewPhotoViewSet,
    ReviewAnalyticsViewSet,
    ReviewTemplateViewSet,
)

router = DefaultRouter()
router.register(r'replies', ReviewReplyViewSet, basename='review-reply')
router.register(r'reports', ReviewReportViewSet, basename='review-report')
router.register(r'photos', ReviewPhotoViewSet, basename='review-photo')
router.register(r'analytics', ReviewAnalyticsViewSet, basename='review-analytics')
router.register(r'templates', ReviewTemplateViewSet, basename='review-template')
router.register(r'', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]