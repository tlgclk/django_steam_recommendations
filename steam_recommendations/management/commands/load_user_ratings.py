from django.core.management.base import BaseCommand
from steam_recommendations.models import UserRating
import csv

class Command(BaseCommand):
    help = 'Loads user ratings from CSV file to the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    playtime_2weeks = int(float(row['playtime_2weeks'])) if row['playtime_2weeks'] else None
                except ValueError:
                    playtime_2weeks = None
                UserRating.objects.create(
                    appid=row['appid'],
                    playtime_forever=row['playtime_forever'],
                    playtime_2weeks=playtime_2weeks,
                    name=row['name'],
                    median_playtime=row['median_playtime'],
                    Assuming_Ratings=row['Assuming_Ratings'],
                    user_id=row['user_id'],
                    user_alias=row['user_alias']
                )
        self.stdout.write(self.style.SUCCESS('User ratings have been successfully loaded'))
