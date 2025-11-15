from django.urls import path 
from . import views


urlpatterns = [
    path('khakpour/login/', views.LoginKhakpourView.as_view(), name='login-khakpour'),
    path('khakpour/verifyotp/', views.VerifyOtpKhakpourView.as_view(), name='verify-otp-khakpour'),
]
