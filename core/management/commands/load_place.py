import json
import os
import uuid
from decimal import Decimal, InvalidOperation
from urllib.parse import urlparse

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from core.models import Place, PlaceImage


class Command(BaseCommand):
    help = 'Загружает/обновляет Place и изображения из JSON-файла (локальный путь или URL)'

    def add_arguments(self, parser):
        parser.add_argument('source', type=str, help='Путь к JSON-файлу или URL')

    def handle(self, *args, **options):
        source = options['source']
        
        self.stdout.write('Начинаем загрузку!\n')

        data = self._load_json(source)

        if isinstance(data, dict) and 'places' in data:
            places_data = data['places']
        elif isinstance(data, dict):
            places_data = [data]
        elif isinstance(data, list):
            places_data = data
        else:
            raise CommandError('Неверный формат JSON: ожидается объект или массив.')

        for place_info in places_data:
            try:
                self._process_place(place_info)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Ошибка при обработке места: {e}'))

    def _load_json(self, source):
        parsed = urlparse(source)
        
        if parsed.scheme in ('http', 'https'):
            try:
                response = requests.get(source, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                raise CommandError(f'Превышено время ожидания при загрузке URL (10 сек): {source}')
            except requests.exceptions.HTTPError as e:
                raise CommandError(f'Ошибка HTTP {e.response.status_code} при загрузке URL: {source}')
            except requests.exceptions.RequestException as e:
                raise CommandError(f'Не удалось загрузить URL (сетевая ошибка): {e}')
            except json.JSONDecodeError as e:
                raise CommandError(f'Невалидный JSON по URL: {e}')
        else:
            try:
                with open(source, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except FileNotFoundError:
                raise CommandError(f'Файл не найден: {source}')
            except json.JSONDecodeError as e:
                raise CommandError(f'Невалидный JSON в файле: {e}')

    def _process_place(self, place_info):
        name = place_info.get('title') or place_info.get('name')
        if not name:
            raise CommandError('В данных места отсутствует поле "title"/"name"')

        coords = place_info.get('coordinates') or {}
        lon_raw = coords.get('lon', coords.get('lng'))
        lat_raw = coords.get('lat')

        if lon_raw is None or lat_raw is None:
            raise CommandError(f'У места "{name}" отсутствуют координаты lon/lat')

        try:
            lon = Decimal(str(lon_raw))
            lat = Decimal(str(lat_raw))
        except (InvalidOperation, ValueError):
            raise CommandError(f'Некорректные координаты у "{name}": lon={lon_raw}, lat={lat_raw}')

        defaults = {
            'shortDesc': place_info.get('description_short', ''),
            'longDesc': place_info.get('description_long', ''),
            'lon': lon,
            'lat': lat,
        }

        place, created = Place.objects.update_or_create(
            name=name,
            defaults=defaults,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Создано место: {place.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Обновлено место: {place.name}'))

        # --- БЛОК ЗАГРУЗКИ ИЗОБРАЖЕНИЙ ---
        imgs = place_info.get('imgs', [])
        for index, img_url in enumerate(imgs):
            if not img_url:
                continue

            # Ищем или создаем запись PlaceImage для этого места и порядкового номера
            place_image, img_created = PlaceImage.objects.get_or_create(
                place=place,
                order=index
            )

            # Если картинка уже есть в базе и файл существует, пропускаем скачивание
            if not img_created and place_image.image:
                continue

            self.stdout.write(f'  Скачиваем изображение {index + 1}: {img_url}...')
            
            try:
                # Скачиваем картинку
                response = requests.get(img_url, timeout=10)
                response.raise_for_status()

                # Пытаемся определить расширение из URL (по умолчанию .jpg)
                parsed_url = urlparse(img_url)
                ext = os.path.splitext(parsed_url.path)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    ext = '.jpg'

                # Генерируем уникальное имя файла
                unique_filename = f"{uuid.uuid4().hex}{ext}"

                # Сохраняем файл через ContentFile
                place_image.image.save(
                    unique_filename,
                    ContentFile(response.content),
                    save=True
                )
                
            except requests.exceptions.RequestException as e:
                # При ошибке скачивания выводим предупреждение, но не ломаем цикл
                self.stderr.write(self.style.WARNING(
                    f'    ⚠️ Не удалось скачать {img_url}: {e}'
                ))
                