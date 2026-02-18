from django.db import models
from decimal import Decimal
from django.conf import settings # 1. ADD THIS IMPORT FOR SAAS SET-UP

class WaterBill(models.Model):

    # 2. ADD THIS FIELD (The "Owner" tag) for SAAS set-up, linking each bill to a specific landlord (user)
    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name="water_bills"

    )

    # Basic Information
    tenant_name = models.CharField(max_length=100)
    room_number = models.CharField(max_length=10)
    billing_date = models.DateField()

    # New field for billing period
    billing_period = models.DateField() 
    
    # Readings
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2)
    current_reading = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Rates and Fees
    rate_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('15.00'))
    fixed_service_fee = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('0.00'))
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Total and Status
    # This is the real database field that was missing/conflicted
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False, default=Decimal('0.00'))
    is_paid = models.BooleanField(default=False)

    @property
    def consumption(self):
        """Calculates usage for display in Admin and Templates."""
        return self.current_reading - self.previous_reading

    def save(self, *args, **kwargs):
        """Calculates total and prevents negative amounts before saving to DB."""
        # Convert fields to Decimal strings to ensure absolute math compatibility
        usage = Decimal(str(self.current_reading)) - Decimal(str(self.previous_reading))
        rate = Decimal(str(self.rate_per_unit))
        fee = Decimal(str(self.fixed_service_fee))
        balance = Decimal(str(self.previous_balance))

        # Core Calculation
        calc_total = (usage * rate) + fee + balance
        
        # Ensure total is never negative and update the database field
        self.total_amount = max(calc_total, Decimal('0.00'))
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant_name} - {self.billing_date}"