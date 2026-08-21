from rest_framework.routers import DefaultRouter

from .views import StockAlertViewSet

router = DefaultRouter()
router.register("alerts", StockAlertViewSet, basename="alert")

urlpatterns = router.urls
