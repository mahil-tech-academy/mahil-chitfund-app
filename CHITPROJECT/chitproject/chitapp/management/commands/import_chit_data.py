import csv
from django.core.management.base import BaseCommand
from chitapp.models import ChitRegistration

class Command(BaseCommand):
    help = 'Imports data from a CSV file into ChitRegistration'

    def handle(self, *args, **kwargs):
        with open('static/csv/chit.csv', mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ChitRegistration.objects.create(
                    chit_Type=row['chit_Type'],
                    chit_Number=row['chit_Number'],
                    name=row['name'],
                    phoneNumber=row['phoneNumber'],
                    address=row['address'],
                    num_Of_Chits=row['num_Of_Chits'],
                    district=row['district']
                )
        self.stdout.write(self.style.SUCCESS('Successfully imported CSV data'))
