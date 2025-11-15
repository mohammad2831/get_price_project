
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

schema_view = get_schema_view(
    openapi.Info(
        title="Khakpour Login API",
        default_version='v1',
      

    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('GetPriceModule/', include('Module_Get_Price.urls')),



path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    
    # ۲. آدرس رابط کاربری Swagger UI
    # آدرس /api/schema/swagger-ui/ را فعال می‌کند
    path(
        'api/schema/swagger-ui/', 
        SpectacularSwaggerView.as_view(url_name='schema'), 
        name='swagger-ui'
    ),

]
