from django.core.management.base import BaseCommand, CommandError
from steam_recommendations.models import Game
import csv

class Command(BaseCommand):
    help = 'Loads games from CSV file to the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Game.objects.create(
                    appid=row['appid'],
                    name=row['name'],
                    release_date=row['release_date'],
                    developer=row['developer'],
                    publisher=row['publisher'],
                    steamspy_tags=row['steamspy_tags'],
                    positive_ratings=row['positive_ratings'],
                    negative_ratings=row['negative_ratings'],
                    median_playtime=row['median_playtime'],
                    price=row['price'],
                    description=row['description'],
                    header_image=row['header_image']
                )
        self.stdout.write(self.style.SUCCESS('Games have been successfully loaded'))
