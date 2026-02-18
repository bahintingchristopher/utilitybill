from django.urls import path
from django.contrib.auth import views as auth_views # Import Django's built-in login/logout
from . import views

app_name = 'water_billing'

urlpatterns = [

    # --- Authentication URLs ---
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('save/', views.save_water_bill, name='save_water'),
    path('mark-paid/<int:bill_id>/', views.mark_water_paid, name='mark_paid'),
    path('get-last-data/', views.get_last_water_data, name='get_last_data'),
    path('edit/<int:bill_id>/', views.edit_water_bill, name='edit_water_bill'),
    path('receipt/<int:bill_id>/', views.water_receipt, name='water_receipt'),

    path('', views.index, name='summary'),
    path('input/', views.input_view, name='input'), # <--- THIS MUST MATCH THE TEMPLATE
     
]