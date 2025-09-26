import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from reviews.models import Category, Genre, GenreTitle, Title, User

CSV_DIR = os.path.join(settings.BASE_DIR, 'static', 'data')

MODEL_CSV = {
    Category: 'category.csv',
    Genre: 'genre.csv',
    Title: 'titles.csv',
    GenreTitle: 'genre_title.csv',
    User: 'users.csv',
}

FK_FIELDS = {
    'category': Category,
    'genre': Genre,
    'title': Title,
    'author': User,
}


def convert_fk(row):
    for key, model in FK_FIELDS.items():
        if key in row:
            row[key] = model.objects.get(pk=row[key])
    return row


class Command(BaseCommand):
    help = 'Load initial data from csv files'

    def handle(self, *args, **options):
        for model, file_name in MODEL_CSV.items():
            path = os.path.join(CSV_DIR, file_name)
            if not os.path.exists(path):
                self.stdout.write(
                    self.style.WARNING(f'Skip {path} – not found')
                )
                continue
            with open(path, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row = convert_fk(row)
                    model.objects.get_or_create(id=row['id'], defaults=row)
            self.stdout.write(
                self.style.SUCCESS(f'Loaded {file_name} → {model.__name__}')
            )
