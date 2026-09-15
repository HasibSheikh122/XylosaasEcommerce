from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import (
    AIRecommendation,
    ChatbotInteraction,
    DemandForecast,
    DynamicPrice,
    CustomerSegment,
    FraudDetection,
    AIContent,
)
from .serializers import (
    AIRecommendationSerializer,
    ChatbotInteractionSerializer,
    DemandForecastSerializer,
    DynamicPriceSerializer,
    CustomerSegmentSerializer,
    FraudDetectionSerializer,
    AIContentSerializer,
)


class BaseAIViewSet(viewsets.ModelViewSet):
    """টেন্যান্ট অনুযায়ী কুয়েরিসেট আইসোলেশনের বেস ভিউসেট"""
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(self.request, 'tenant'):
            qs = qs.filter(tenant=self.request.tenant)
        return qs

    def perform_create(self, serializer):
        kwargs = {}
        if hasattr(self.request, 'tenant'):
            kwargs['tenant'] = self.request.tenant
        serializer.save(**kwargs)


class AIRecommendationViewSet(BaseAIViewSet):
    queryset = AIRecommendation.objects.select_related('product', 'customer').all()
    serializer_class = AIRecommendationSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['customer', 'product', 'clicked', 'purchased']
    ordering_fields = ['score', 'created_at']
    ordering = ['-score']

    @action(detail=True, methods=['post'], url_path='mark-clicked')
    def mark_clicked(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.clicked = True
        recommendation.save(update_fields=['clicked'])
        return Response({'status': 'marked as clicked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='mark-viewed')
    def mark_viewed(self, request, pk=None):
        recommendation = self.get_object()
        recommendation.viewed = True
        recommendation.save(update_fields=['viewed'])
        return Response({'status': 'marked as viewed'}, status=status.HTTP_200_OK)


class ChatbotInteractionViewSet(BaseAIViewSet):
    queryset = ChatbotInteraction.objects.select_related('customer').all()
    serializer_class = ChatbotInteractionSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['session_id', 'intent', 'was_helpful']
    search_fields = ['question', 'response']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], url_path='feedback')
    def feedback(self, request, pk=None):
        interaction = self.get_object()
        was_helpful = request.data.get('was_helpful')
        if was_helpful is not None:
            interaction.was_helpful = bool(was_helpful)
            interaction.save(update_fields=['was_helpful'])
            return Response({'status': 'feedback recorded'}, status=status.HTTP_200_OK)
        return Response({'error': 'was_helpful field is required'}, status=status.HTTP_400_BAD_REQUEST)


class DemandForecastViewSet(BaseAIViewSet):
    queryset = DemandForecast.objects.select_related('product').all()
    serializer_class = DemandForecastSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = {'product': ['exact'], 'forecast_date': ['exact', 'gte', 'lte']}
    ordering_fields = ['forecast_date', 'predicted_quantity']
    ordering = ['forecast_date']


class DynamicPriceViewSet(BaseAIViewSet):
    queryset = DynamicPrice.objects.select_related('product').all()
    serializer_class = DynamicPriceSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['product', 'strategy_used']
    ordering = ['-created_at']


class CustomerSegmentViewSet(BaseAIViewSet):
    queryset = CustomerSegment.objects.all()
    serializer_class = CustomerSegmentSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['name']


class FraudDetectionViewSet(BaseAIViewSet):
    queryset = FraudDetection.objects.select_related('order', 'reviewed_by').all()
    serializer_class = FraudDetectionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['risk_level', 'is_flagged', 'is_reviewed', 'order']
    ordering_fields = ['risk_score', 'created_at']
    ordering = ['-risk_score']

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        fraud = self.get_object()
        fraud.is_reviewed = True
        fraud.reviewed_by = request.user
        fraud.is_flagged = request.data.get('is_flagged', fraud.is_flagged)
        fraud.save(update_fields=['is_reviewed', 'reviewed_by', 'is_flagged'])
        return Response({'status': 'fraud record reviewed', 'is_flagged': fraud.is_flagged})


class AIContentViewSet(BaseAIViewSet):
    queryset = AIContent.objects.select_related('approved_by').all()
    serializer_class = AIContentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['content_type', 'is_approved']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        content = self.get_object()
        content.is_approved = True
        content.approved_by = request.user
        content.save(update_fields=['is_approved', 'approved_by'])
        return Response({'status': 'content approved'})