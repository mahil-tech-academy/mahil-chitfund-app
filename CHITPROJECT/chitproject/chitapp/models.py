from django.db import models
from datetime import datetime

class ChitRegistration(models.Model):

    chit_Type = models.CharField(max_length=10)
    chit_Number = models.CharField(max_length=20, unique=True,blank=True)
    name = models.CharField(max_length=100)
    phoneNumber = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    village = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    num_Of_Chits = models.IntegerField()
    whatsapp = models.CharField(max_length=15)
    
    def __str__(self):
        return f"{self.chit_Type} - {self.chit_Number}"
    
class ChitPayment(models.Model):

    chit_type = models.CharField(max_length=100, unique=True)
    chit_amount = models.IntegerField(default=0)
    total_people = models.IntegerField(default=0)
    total_weeks_now = models.IntegerField(default=0)
    total_weeks_paid = models.IntegerField(default=0)
    total_amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expected_paid_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    pending_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_date = models.DateField(default=datetime.today)
    

    def __str__(self):
        return f"{self.chit_type} Summary"

class Payment(models.Model):
    
    payment_id = models.AutoField(auto_created = True,primary_key=True)
    chit_id = models.IntegerField(null=True, blank=True)
    chitnumber = models.CharField(max_length=20,null=False, blank=False)
    payment_weeks = models.IntegerField(null=True, blank=True)
    amount_per_week = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    overdue_fees = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cash_received = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    total_paid_week = models.IntegerField(default=0)
    timestamp = models.DateTimeField(null=True, blank=True)
    num_of_chits = models.IntegerField(null=True, blank=True)
    

    def save(self, *args, **kwargs):
        if self.chit_id:  
            chit = ChitRegistration.objects.filter(id=self.chit_id).first()
            if chit:
                self.chitnumber = chit.chit_Number  
        super().save(*args, **kwargs)  

    def __str__(self):
        return f"{self.chit_id} - {self.chitnumber} : {self.payment_weeks} Weeks"
    
class WhatsAppMessageLog(models.Model):
    chit_number = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    message = models.TextField()
    sent_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[('sent', 'Sent'), ('failed', 'Failed')])  
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.chit_number} - {self.name}"

    
class AdminConfig(models.Model):
    
    key = models.CharField(max_length=255)
    value = models.TextField()

    def __str__(self):
        return f"{self.key}: {self.value}"
    
