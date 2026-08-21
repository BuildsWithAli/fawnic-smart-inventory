from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("inventory.urls")),
    path("api/", include("partners.urls")),
    path("api/", include("transactions.urls")),
    path("api/", include("orders.urls")),
    path("api/", include("ai_assistant.urls")),
    path("api/dashboard/", include("dashboard.urls")),
]
