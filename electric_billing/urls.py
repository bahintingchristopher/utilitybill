from django.urls import path
from django.contrib.auth import views as auth_views # Import Django's built-in login/logout
from . import views

app_name = 'electric_billing'

 

urlpatterns = [

      # --- Authentication URLs ---
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('', views.index, name='summary'),
    # Make sure this line exists and the name is EXACTLY 'input'
    path('input/', views.input_view, name='input'),

    path('save/', views.save_electric_bill, name='save_electric'),
    path('get-last-data/', views.get_last_electric_data, name='get_last_data'),
    path('receipt/<int:bill_id>/', views.electric_receipt, name='electric_receipt'),
    # Use this one for consistency:
    path('edit/<int:bill_id>/', views.edit_electric_bill, name='edit_electric_bill'),
    path('mark-paid/<int:bill_id>/', views.mark_paid_view, name='mark_paid'), 
]