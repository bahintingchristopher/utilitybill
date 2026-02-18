from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from .models import ElectricBill
from decimal import Decimal
from django.http import JsonResponse
from django.db.models import Sum
from electric_billing.models import ElectricBill # Imported for unpaid total calculation
from django.contrib.auth.decorators import login_required #login required decorator for each landlord to access only their data
from datetime import datetime  # Make sure this is imported at the very top for the billing_summary view
 

@login_required
def get_last_electric_data(request):
    tenant_name = request.GET.get('name')
    # Fixed: Orders by ID to get the absolute latest entry
    last_bill = ElectricBill.objects.filter(landlord=request.user, tenant_name=tenant_name).order_by('-id').first()
    
    data = {
        'last_reading': float(last_bill.current_reading) if last_bill else 0,
        'room_number': last_bill.room_number if last_bill else ''
    }
    return JsonResponse(data)

@login_required
def save_electric_bill(request):
    if request.method == "POST":
        # Capture from the HTML form names
        tenant = request.POST.get('e_tenant_name')
        room = request.POST.get('e_room_number')
        billing_date = request.POST.get('billing_date')
        prev = Decimal(request.POST.get('e_prev') or '0')
        curr = Decimal(request.POST.get('e_curr') or '0')
        # Captured from the new Rate field we added
        rate = Decimal(request.POST.get('e_rate') or '13.65') 

        # added to capture billing period
        billing_period = request.POST.get('billing_period')

        new_bill = ElectricBill.objects.create(
            landlord=request.user,  # Link the bill to the logged-in landlord for SAAS set-up
            tenant_name=tenant,
            room_number=room,
            billing_date=billing_date,
            previous_reading=prev,
            billing_period=billing_period, # added billing period
            current_reading=curr,
            rate_per_kwh=rate, 
            is_paid=False
        )
        
        messages.success(request, f"Electric bill saved for {new_bill.tenant_name}")
        
        # Redirect to print the receipt in a new tab
        return redirect(f'/?print_electric={new_bill.id}')
    
    return redirect('/?tab=dash_home')

@login_required
def electric_receipt(request, bill_id):
    bill = get_object_or_404(ElectricBill, id=bill_id, landlord=request.user)
    
   # Get the queryset for OTHER unpaid electric bills
    unpaid_queryset = ElectricBill.objects.filter(landlord=request.user,
        tenant_name__iexact=bill.tenant_name, 
        is_paid=False
    ).exclude(id=bill_id)
    unpaid_total = unpaid_queryset.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0.00')

    # 2. Calculate the number of unpaid bills
    unpaid_count = unpaid_queryset.count()

    context = {
        'bill': bill,
        'unpaid_total': unpaid_total,
        'unpaid_count': unpaid_count, # The number of bills
        'grand_total': bill.total_amount + unpaid_total,
    }
    return render(request, 'electric_billing/electric_receipt.html', context)

 
@login_required
def mark_paid_view(request, bill_id):
    if request.method == "POST":
        bill = get_object_or_404(ElectricBill, id=bill_id, landlord=request.user)
        bill.is_paid = True
        bill.save()
        messages.success(request, f"Electric bill for {bill.tenant_name} marked as PAID.")
    return redirect('/?tab=unpaid_account')



@login_required
def index(request):
    # This handles {% url 'electric_billing:summary' %}
    bills = ElectricBill.objects.filter(landlord=request.user).order_by('-billing_date')
    
    # We must add current_year and active_tab so main.html doesn't crash
    context = {
        'bills': bills, 
        'type': 'electric',
        'current_year': datetime.now().year,
        'active_tab': 'dashboard'
    }
    return render(request, 'main.html', context)


@login_required
def input_view(request):
    # This handles {% url 'electric_billing:input' %}
    # You can point this to your existing input template
    return render(request, 'electric_input.html')


@login_required
def edit_electric_bill(request, bill_id):
    bill = get_object_or_404(ElectricBill, id=bill_id, landlord=request.user)
    
    if request.method == "POST":
        # Capture the updated values from the edit form 
        bill.previous_reading = Decimal(request.POST.get('prev') or '0')
        bill.current_reading = Decimal(request.POST.get('curr') or '0')
    
        
        # We also capture the rate in case you need to fix a pricing error
        bill.rate_per_kwh = Decimal(request.POST.get('rate') or '13.65')
        
        bill.is_paid = request.POST.get('status') == 'PAID'
        
        # Save triggers the model's logic to recalculate the total_amount
        bill.save()
        
        messages.success(request, f"Electric record for {bill.tenant_name} updated successfully!")
        
        # Redirect back to the search tab so you can see the updated result
        return redirect('/?tab=dash_home')

    # If it's a GET request, show the edit page
    return render(request, 'edit_form.html', {'bill': bill, 'type': 'electric'})



