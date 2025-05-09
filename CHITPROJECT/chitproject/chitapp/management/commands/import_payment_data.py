import csv
from django.core.management.base import BaseCommand
from chitapp.models import Payment
from decimal import Decimal
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports data from a CSV file into Payment'

    def handle(self, *args, **kwargs):
        with open('static/csv/chitpayment_id_merged.csv', mode='r') as file:
            reader = csv.DictReader(file)
            print("CSV Columns: ", reader.fieldnames)

            for row in reader:
                
                timestamp_str = row['timestamp']
                if len(timestamp_str) == 8: 
                    timestamp = datetime.strptime(timestamp_str, '%y.%m.%d')
                elif len(timestamp_str) == 17: 
                    timestamp = datetime.strptime(timestamp_str, '%y.%m.%d %H:%M:%S')
                else:
                    timestamp = None 

                Payment.objects.create(
                    chit_id=row['chit_id'] if 'chit_id' in row and row['chit_id'] else None,
                    chitnumber=row['chitnumber'],
                    payment_weeks=row['payment_weeks'] if 'payment_weeks' in row and row['payment_weeks'] else None,
                    amount_per_week=Decimal(row['amount_per_week']),
                    total_amount=Decimal(row['total_amount']),
                    overdue_fees=Decimal(row['overdue_fees']) if 'overdue_fees' in row and row['overdue_fees'] else None,
                    cash_received=Decimal(row['cash_received']) if 'cash_received' in row else Decimal(0),
                    balance=Decimal(row['balance']),
                    total_paid_week=row['total_paid_week'],
                    timestamp=timestamp,  
                    num_of_chits=row['num_of_chits'] if 'num_of_chits' in row and row['num_of_chits'] else None
                )

        self.stdout.write(self.style.SUCCESS('Successfully imported CSV data into Payment'))
