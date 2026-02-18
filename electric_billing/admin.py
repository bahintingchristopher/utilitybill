from django.contrib import admin
from .models import ElectricBill

@admin.register(ElectricBill)
class ElectricBillAdmin(admin.ModelAdmin):
    # Added 'is_paid' to the end of this list
    list_display = ('billing_date', 'tenant_name', 'room_number', 'previous_reading', 'current_reading', 'total_amount', 'is_paid')
    
    # Now this will work because 'is_paid' is visible in the list above
    list_editable = ('is_paid',)

    class Media:
        js = ('water_billing/js/auto_fill.js',)