from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import StoreSettingsSerializer, StoreCategorySerializer
from .services import StoreService
from .models import StoreCategory

class StoreSettingsViewSet(viewsets.GenericViewSet, viewsets.mixins.UpdateModelMixin):
    serializer_class = StoreSettingsSerializer
    
    def get_object(self):
        return StoreService.get_settings(self.request.user.tenant)

    @action(detail=False, methods=['patch'])
    def update_branding(self, request):
        settings = StoreService.update_branding(self.request.user.tenant, request.data)
        return Response(StoreSettingsSerializer(settings).data)

class StoreCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = StoreCategorySerializer

    def get_queryset(self):
        return StoreCategory.objects.filter(tenant=self.request.user.tenant).select_related('parent')

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)