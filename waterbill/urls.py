from django.contrib import admin
from django.urls import path, include
from waterbill import views as main_views
from django.contrib.auth import views as auth_views
from water_billing import views as water_views


from . import views # this is to import from main views.py  


urlpatterns = [
    # --- ADMIN & AUTHENTICATION ---
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # --- MAIN dashboard (The HOMEPAGE) ---
    path('', main_views.billing_summary, name='billing_summary'),

    # SHARED API ENDPOINTS
    path('get-tenant-info/', main_views.get_tenant_info, name='get_tenant_info'),
    path('mark-paid/<int:bill_id>/<str:bill_type>/', main_views.mark_bill_paid, name='mark_bill_paid'),
    path('save-all-bills/', main_views.save_all_bills, name='save_all_bills'),


   
    # --- SPECIALIZED APP LOGIC ---
    path('water-billing/', include('water_billing.urls')),
    path('electric-billing/', include('electric_billing.urls')),

    # FOR NEW ACCOUNT / USER REGISTRATION (SAAS SET-UP)
    path('register/', views.register_view, name='register'),


    

 
    # PASSWORD RESET URLS (SAAS SET-UP)
    # 1. Page to enter email
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    
    # 2. Confirmation email sent page
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    
    # 3. The actual link sent to the email
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    
    # 4. Success page
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),



    # This is the specific line that triggers that "Create New Password" page
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), 
         name='password_reset_confirm'),
         
    # This is where the user goes AFTER successfully changing the password
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), 
         name='password_reset_complete'),



]




 