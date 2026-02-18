from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import WaterBill

@admin.register(WaterBill)
class WaterBillAdmin(admin.ModelAdmin):
    list_display = ('tenant_name', 
                    'room_number', 
                    'billing_date', 
                    'previous_reading', 
                    'current_reading', 
                    'consumption', 
                    'total_amount',
                    'is_paid'
                    )
    list_editable = ('is_paid',)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        
        # Look for the very last bill created to get the reading
        tenant = request.GET.get('tenant_name', None)
        
        if tenant:
            # Set the new "previous" reading to the last "current" reading
            last_bill = (WaterBill.objects.filter(tenant_name__iexact=tenant,
                        current_reading__gt=0)
                        .order_by('-billing_date', '-id')
                        .first())
        
        else:
             #fall back to the most recent bill overall
             last_bill = (WaterBill.objects.filter(current_reading__gt=0)
                        .order_by('-billing_date', '-id')
                        .first())


        if last_bill:
                initial['previous_reading'] = last_bill.current_reading                         
            
        return initial
    
    # This tells Django to load your JS file on the 'Add/Change' pages
    class Media:
        # Note: Do NOT start with a slash. 
        # It must match the path AFTER the 'static' folder.
        js = ('water_billing/js/auto_fill.js',)

    # Add these lines to customize the Django Admin interface
admin.site.site_header = "Welcome to the Utility Management Portal"
admin.site.site_title = "Utilities Admin Portal"
admin.site.index_title = "UTILITIES ADMIN PORTAL"