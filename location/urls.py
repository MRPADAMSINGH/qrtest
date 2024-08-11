from django.urls import path
from . import views

urlpatterns = [
    # path('location/', views.verify_location_qr_code, name='request_location'),
        # path('location-request/', views.location_request, name='location_request'),
    path('verify-location/', views.verify_location_qr_code, name='verify_location'),
        # path('user-location', views.user_location_info, name='user_location_info'),
    # path('save-location', views.save_location, name='save_location'),
     path('test1/', views.test1_form, name='test1_form'),
     path('success/', views.success, name='success'),
    
]
