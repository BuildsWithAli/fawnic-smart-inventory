from rest_framework.routers import DefaultRouter

from .views import PurchaseViewSet, SaleViewSet

router = DefaultRouter()
router.register("purchases", PurchaseViewSet, basename="purchase")
router.register("sales", SaleViewSet, basename="sale")

urlpatterns = router.urls
