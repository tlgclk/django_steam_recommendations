from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from steam_recommendations.models import UserAliasMapping  # myapp.models'ı kendi uygulamanızın models.py dosyasındaki isimle değiştirin
import csv

class Command(BaseCommand):
    help = 'Loads user alias mappings from CSV file to a separate table in the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user_id = row['user_id']
                user_alias = row['user_alias']
                
                # user_alias'ı kontrol et, eğer daha önce eklenmediyse ekle
                if not UserAliasMapping.objects.filter(user_alias=user_alias).exists():
                    UserAliasMapping.objects.create(user_id=user_id, user_alias=user_alias)

        self.stdout.write(self.style.SUCCESS('User alias mappings have been successfully loaded'))
