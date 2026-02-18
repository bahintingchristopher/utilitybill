from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.contrib import messages
from water_billing.models import WaterBill
from electric_billing.models import ElectricBill
from django.http import JsonResponse
from decimal import Decimal
from django.db.models import Q
from itertools import chain # Added for combining querysets
import calendar # Added for month name conversion
from datetime import datetime

# FOR NEW USER REGISTRATION (SAAS SET-UP)
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User



# this is very IMPORTANT so that the login page appears if user is not logged in
from django.contrib.auth.decorators import login_required  # Added for authentication


@login_required
def billing_summary(request):
    """Dashboard with unpaid/paid totals and month/year/name search."""
    now = datetime.now()
    query = request.GET.get('q', '').strip() 
    month = request.GET.get('month')
    year = request.GET.get('year')
    u_type = request.GET.get('u_type', 'both') 
    
    # 1. FIX: Smarter Month Name Logic
    if month and month.isdigit():
        month_name = calendar.month_name[int(month)]
    else:
        # Instead of "CURRENT", show the actual month (e.g., "February")
        month_name = now.strftime("%B") 

    # 2. Base QuerySets
    water_qs = WaterBill.objects.filter(landlord=request.user)
    electric_qs = ElectricBill.objects.filter(landlord=request.user)

    # 3. Apply Date Filters
    if month and month.isdigit():
        water_qs = water_qs.filter(billing_date__month=month)
        electric_qs = electric_qs.filter(billing_date__month=month)
    
    if year and year.isdigit():
        water_qs = water_qs.filter(billing_date__year=year)
        electric_qs = electric_qs.filter(billing_date__year=year)

    # 4. History logic (Keep your search logic)
    if query:
        history_water = water_qs.filter(tenant_name__icontains=query).order_by('-billing_date', '-id')
        history_electric = electric_qs.filter(tenant_name__icontains=query).order_by('-billing_date', '-id')
    else:
        history_water = water_qs.order_by('-billing_date', '-id')[:5]
        history_electric = electric_qs.order_by('-billing_date', '-id')[:5]

    # 5. Global Unpaid/Paid (Isolated by User)
    unpaid_w_qs = WaterBill.objects.filter(landlord=request.user, is_paid=False)
    unpaid_e_qs = ElectricBill.objects.filter(landlord=request.user, is_paid=False)
    paid_w_qs = WaterBill.objects.filter(landlord=request.user, is_paid=True)
    paid_e_qs = ElectricBill.objects.filter(landlord=request.user, is_paid=True)

    # 6. Calculate Totals (Double check field names in your models!)
    total_unpaid_w = unpaid_w_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_unpaid_e = unpaid_e_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid_w = paid_w_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_paid_e = paid_e_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'query': query,
        'u_type': u_type,
        'selected_month_name': month_name,
        'selected_month': month, 
        'selected_year': year,
        'current_year': now.year, # This fixes the VariableDoesNotExist error
        'history_water': history_water,
        'history_electric': history_electric,
        'unpaid_water': unpaid_w_qs.order_by('-billing_date'),
        'unpaid_electric': unpaid_e_qs.order_by('-billing_date'),
        'paid_water': paid_w_qs.order_by('-billing_date'),
        'paid_electric': paid_e_qs.order_by('-billing_date'),
        'grand_total_unpaid': total_unpaid_w + total_unpaid_e,
        'grand_total_paid': total_paid_w + total_paid_e,
        'active_tab': request.GET.get('tab', 'dash_home'),
    }

    return render(request, 'main.html', context)

@login_required
def mark_bill_paid(request, bill_id, bill_type):
    """
    Orchestrator function: decides which model to update 
    based on the URL parameter 'bill_type'.
    """
    if bill_type == 'water':
        bill = get_object_or_404(WaterBill, id=bill_id, landlord=request.user)
    elif bill_type == 'electric':
        bill = get_object_or_404(ElectricBill, id=bill_id, landlord=request.user)
    else:
        messages.error(request, "Invalid bill type.")
        return redirect('billing_summary')

    bill.is_paid = True
    bill.save()
    messages.success(request, f"{bill_type.capitalize()} bill for {bill.tenant_name} marked as PAID.")
    
    # Returns to the unpaid tab on the dashboard
    return redirect('/?tab=unpaid_account')


@login_required
def get_tenant_info(request):
    """AJAX helper for tenant auto-fill; READ ONLY."""
    tenant_name = request.GET.get('tenant_name')
    if not tenant_name:
        return JsonResponse({}, status=400)

    data = {}
    last_water = WaterBill.objects.filter(landlord=request.user, tenant_name__iexact=tenant_name).order_by('-billing_date').first()
    last_electric = ElectricBill.objects.filter(landlord=request.user, tenant_name__iexact=tenant_name).order_by('-billing_date').first()

    if last_water:
        data['room_number'] = last_water.room_number
        data['w_prev'] = float(last_water.current_reading)
    if last_electric:
        data['e_prev'] = float(last_electric.current_reading)
        if 'room_number' not in data:
             data['room_number'] = last_electric.room_number

    return JsonResponse(data)


@login_required
def save_all_bills(request):
    """Logic for the 'New Renter Setup' form."""
    if request.method == "POST":
        tenant = request.POST.get('tenant_name')
        room = request.POST.get('room_number')
        date = request.POST.get('billing_date')
        
         # Fetch the landlord's custom rates (fallback to defaults if profile doesn't exist)
         
        w_rate = Decimal(request.POST.get('w_rate') or '5.00')
        e_rate = Decimal(request.POST.get('e_rate') or '14.00')

        # Initial Readings provided by the admin
        w_start = Decimal(request.POST.get('w_curr') or '0')
        e_start = Decimal(request.POST.get('e_curr') or '0')


        # 1. Create initial Water record (0 consumption)
        WaterBill.objects.create(
            landlord=request.user,  # <--- this is to associate the bill with the logged-in landlord
            tenant_name=tenant,
            room_number=room,
            billing_date=date,
            billing_period=date, # <--- Assuming same as billing date for initial setup
            previous_reading=w_start,
            current_reading=w_start, # Same as previous so consumption is 0
            rate_per_unit=w_rate, # <--- USES DYNAMIC RATE
            is_paid=True # Usually marked paid as it's just a starting point
        )

        # 2. Create initial Electric record (0 consumption)
        ElectricBill.objects.create(
            tenant_name=tenant,
            landlord=request.user,  # <--- This is to associate the bill with the logged-in landlord
            room_number=room,
            billing_date=date,
            billing_period=date, # <--- Assuming same as billing date for initial setup
            rate_per_kwh=e_rate, # <--- USES DYNAMIC RATE
            previous_reading=e_start,
            current_reading=e_start,
            consumption=0,
            total_amount=0,
            is_paid=True
        )

        messages.success(request, f"New account created for {tenant} at Room {room}")
        return redirect('/?tab=dash_home')
    
    return redirect('/')






# 1. THE CUSTOM FORM (Collects Username, Email, and Password)
class LandlordRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Required for future password recovery.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',)

# 2. THE REGISTRATION VIEW
def register_view(request):
    if request.method == "POST":
        form = LandlordRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in automatically
            messages.success(request, f"Account created successfully! Welcome, {user.username}.")
            return redirect('billing_summary') # Redirects to your main dashboard
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = LandlordRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})