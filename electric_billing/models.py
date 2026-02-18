from django.db import models
from decimal import Decimal
from django.conf import settings # 1. ADD THIS IMPORT FOR SAAS SET-UP

class ElectricBill(models.Model):
    # 2. ADD THIS FIELD (The "Owner" tag) for SAAS set-up, linking each bill to a specific landlord (user)
    landlord = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    tenant_name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20)
    billing_date = models.DateField()
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2)
    current_reading = models.DecimalField(max_digits=10, decimal_places=2)

    # Optional field for billing period description
    # billing_period = models.CharField(max_length=50, blank=True, null=True)
    billing_period = models.DateField(blank=True, null=True)

    
    rate_per_kwh = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('13.65'))
    fixed_service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)

    @property
    def consumption(self):
        return self.current_reading - self.previous_reading

    def save(self, *args, **kwargs):
        usage = self.current_reading - self.previous_reading
        calc_total = (usage * self.rate_per_kwh) + self.fixed_service_fee + self.previous_balance
        self.total_amount = max(calc_total, Decimal('0.00'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant_name} - {self.billing_date}"