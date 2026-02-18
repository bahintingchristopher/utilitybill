from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import WaterBill
from datetime import datetime, date #newly added for billing period
from dateutil.relativedelta import relativedelta #newly added for billing period
from decimal import Decimal
from django.http import JsonResponse
from django.db.models import Sum
from django.contrib.auth.decorators import login_required #login required decorator for each landlord to access only their data
 
@login_required
def index(request):
    bills = WaterBill.objects.filter(landlord=request.user).order_by('-billing_date', '-id')
    unpaid_water = WaterBill.objects.filter(landlord=request.user, is_paid=False)
    
    grand_total_unpaid = unpaid_water.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    grand_total_paid = WaterBill.objects.filter(landlord=request.user, is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'bills': bills,
        'unpaid_water': unpaid_water,
        'grand_total_unpaid': grand_total_unpaid,
        'grand_total_paid': grand_total_paid,              
        'active_tab': request.GET.get('tab', 'dashboard'), 
    }
    return render(request, 'main.html', context)

@login_required
def get_last_water_data(request):
    tenant_name = request.GET.get('name')
    last_bill = WaterBill.objects.filter(landlord=request.user,
                tenant_name=tenant_name).order_by('-id').first()
    
    data = {
        'last_reading': float(last_bill.current_reading) if last_bill else 0,
        'room_number': last_bill.room_number if last_bill else ''
    }
    return JsonResponse(data)

@login_required 
def save_water_bill(request):
    if request.method == "POST":
        tenant = request.POST.get('w_tenant_name')
        room = request.POST.get('w_room_number')
        billing_date = request.POST.get('billing_date')
        
        # 1. Get the date object
        billing_date_obj = datetime.strptime(billing_date, '%Y-%m-%d').date()

        # 2. Get the period from JS, or calculate it here as a backup
        # This ensures it is NEVER "Not Calculated"
        period = request.POST.get('billing_period')
        if not period:
            last_month = billing_date_obj - relativedelta(months=1)
            period = last_month.strftime('%B %Y')

        prev = Decimal(request.POST.get('w_prev') or '0')
        curr = Decimal(request.POST.get('w_curr') or '0')
        rate = Decimal(request.POST.get('w_rate') or '15.00') 

        # 3. Save to Database
        new_bill = WaterBill.objects.create(
            landlord=request.user,  # <-- ADDED FOR SAAS SET-UP
            tenant_name=tenant,
            room_number=room,
            billing_date=billing_date,
            billing_period=period,  # Uses our fixed 'period' variable
            previous_reading=prev,
            current_reading=curr,
            rate_per_unit=rate,
            is_paid=False
        )
        
        # 4. Success Message (Fixed the variable name here)
        messages.success(request, f"Water bill saved for {new_bill.tenant_name}. Period: {period}")

        # 5. Redirect to print the receipt in a new tab   
        return redirect(f"/?print_water={new_bill.id}")
        
    return redirect('/?tab=dash_home')


@login_required
def edit_water_bill(request, bill_id):
    bill = get_object_or_404(WaterBill, id=bill_id, landlord=request.user)  # Ensure the bill belongs to the logged-in landlord
    if request.method == "POST":
        bill.previous_reading = Decimal(request.POST.get('prev') or '0')
        bill.current_reading = Decimal(request.POST.get('curr') or '0')
        bill.rate_per_unit = Decimal(request.POST.get('rate') or bill.rate_per_unit)
        bill.is_paid = request.POST.get('status') == 'PAID'
        bill.save()
        messages.success(request, f"Water record for {bill.tenant_name} updated!")
        return redirect('/?tab=dash_home')

    return render(request, 'edit_form.html', {'bill': bill, 'type': 'water'})

@login_required
def mark_water_paid(request, bill_id):
    bill = get_object_or_404(WaterBill, id=bill_id, landlord=request.user)  # Ensure the bill belongs to the logged-in landlord
    bill.is_paid = True
    bill.save()
    messages.success(request, f"Water bill marked as paid.")
    return redirect('/?tab=unpaid_account')

@login_required
def water_receipt(request, bill_id):
    bill = get_object_or_404(WaterBill, id=bill_id, landlord=request.user)  # Ensure the bill belongs to the logged-in landlord
    
    # Get the queryset of other unpaid bills
    unpaid_queryset = WaterBill.objects.filter(landlord=request.user,
        tenant_name__iexact=bill.tenant_name, 
        is_paid=False
    ).exclude(id=bill_id)
    unpaid_count = unpaid_queryset.count()

    unpaid_total = unpaid_queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    context = {
        'bill': bill,
        'unpaid_total': unpaid_total,
        'unpaid_count': unpaid_count,
        'grand_total': bill.total_amount + unpaid_total,
    }
    return render(request, 'water_billing/water_receipt.html', context)

# --- THIS IS THE VIEW DJANGO WAS COMPLAINING ABOUT ---
@login_required
def input_view(request):
    unpaid_water = WaterBill.objects.filter(landlord=request.user, is_paid=False)
    context = {
        'bills': WaterBill.objects.filter(landlord=request.user).order_by('-id'),
        'unpaid_water': unpaid_water,
        'grand_total_unpaid': unpaid_water.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'grand_total_paid': WaterBill.objects.filter(landlord=request.user, is_paid=True).aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
        'active_tab': 'input_water' 
    }
    return render(request, 'main.html', context)


 