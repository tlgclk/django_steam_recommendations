from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import csv

class Command(BaseCommand):
    help = 'Loads users from CSV file to the database and creates Django users'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_id = row['user_id']
                user = User.objects.create_user(username=user_id, password='1')
                user.save()
                # Veritabanındaki kullanıcı ID'si ve kullanıcı adını eşleştirme
                self.stdout.write(self.style.SUCCESS(f"User created with ID: {user.id} and username: {user.username}"))
        self.stdout.write(self.style.SUCCESS('Users have been successfully loaded and created'))
