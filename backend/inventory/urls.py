from rest_framework.routers import DefaultRouter

from .views import BrandViewSet, CategoryViewSet, ProductViewSet, StockAdjustmentViewSet, WarehouseViewSet

router = DefaultRouter()
router.register("products", ProductViewSet, basename="product")
router.register("brands", BrandViewSet, basename="brand")
router.register("categories", CategoryViewSet, basename="category")
router.register("warehouses", WarehouseViewSet, basename="warehouse")
router.register("stock-adjustments", StockAdjustmentViewSet, basename="stock-adjustment")

urlpatterns = router.urls
