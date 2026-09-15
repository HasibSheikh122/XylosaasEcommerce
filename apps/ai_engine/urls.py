from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AIRecommendationViewSet,
    ChatbotInteractionViewSet,
    DemandForecastViewSet,
    DynamicPriceViewSet,
    CustomerSegmentViewSet,
    FraudDetectionViewSet,
    AIContentViewSet,
)

router = DefaultRouter()
router.register(r'recommendations', AIRecommendationViewSet, basename='ai-recommendation')
router.register(r'chatbot', ChatbotInteractionViewSet, basename='ai-chatbot')
router.register(r'forecasts', DemandForecastViewSet, basename='ai-forecast')
router.register(r'dynamic-pricing', DynamicPriceViewSet, basename='ai-dynamic-pricing')
router.register(r'segments', CustomerSegmentViewSet, basename='ai-segment')
router.register(r'fraud-detections', FraudDetectionViewSet, basename='ai-fraud')
router.register(r'contents', AIContentViewSet, basename='ai-content')

urlpatterns = [
    path('', include(router.urls)),
]