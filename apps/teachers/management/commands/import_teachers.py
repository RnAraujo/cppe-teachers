import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError
from apps.teachers.models import Teacher

class Command(BaseCommand):
    help = 'Importa profesores desde CSV. Columnas esperadas: dni, first_name, last_name, registration_code, is_enabled (opcional: mother_last_name, pero no se usa)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Ruta al archivo CSV')
        parser.add_argument('--delimiter', type=str, default=',', help='Delimitador (por defecto ",")')
        parser.add_argument('--update', action='store_true', help='Actualizar registros existentes')
        parser.add_argument('--dry-run', action='store_true', help='Simular sin guardar')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        delimiter = options['delimiter']
        update = options['update']
        dry_run = options['dry_run']

        if not os.path.isfile(csv_file):
            raise CommandError(f'Archivo "{csv_file}" no existe.')

        total = created = updated = errors = skipped = 0

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            expected = {'dni', 'first_name', 'last_name', 'registration_code', 'is_enabled'}
            if not expected.issubset(reader.fieldnames):
                missing = expected - set(reader.fieldnames)
                raise CommandError(f'Faltan columnas: {", ".join(missing)}')

            self.stdout.write(self.style.SUCCESS(f'Iniciando importación desde {csv_file}...'))
            if dry_run:
                self.stdout.write(self.style.WARNING('--- MODO DRY RUN ---'))

            for row in reader:
                total += 1
                dni = row.get('dni', '').strip()
                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()
                registration_code = row.get('registration_code', '').strip()
                is_enabled_raw = row.get('is_enabled', '').strip().lower()

                if not all([dni, first_name, last_name, registration_code]):
                    self.stderr.write(self.style.ERROR(f'Fila {total}: Datos incompletos, se omite.'))
                    skipped += 1
                    continue
                if not dni.isdigit() or len(dni) != 8:
                    self.stderr.write(self.style.ERROR(f'Fila {total}: DNI "{dni}" inválido.'))
                    errors += 1
                    continue

                is_enabled = is_enabled_raw in ('1', 'true', 'yes', 'si')
                data = {
                    'dni': dni,
                    'first_name': first_name,
                    'last_name': last_name,
                    'registration_code': registration_code,
                    'is_enabled': is_enabled,
                }

                if dry_run:
                    self.stdout.write(f'[DRY-RUN] {data}')
                    continue

                try:
                    teacher = Teacher.objects.filter(dni=dni).first()
                    if teacher and update:
                        for key, value in data.items():
                            setattr(teacher, key, value)
                        teacher.save()
                        updated += 1
                        self.stdout.write(self.style.SUCCESS(f'Actualizado: {dni}'))
                    elif teacher and not update:
                        self.stdout.write(self.style.WARNING(f'DNI {dni} ya existe. Use --update.'))
                        skipped += 1
                    else:
                        Teacher.objects.create(**data)
                        created += 1
                        self.stdout.write(self.style.SUCCESS(f'Creado: {dni}'))
                except IntegrityError as e:
                    self.stderr.write(self.style.ERROR(f'Error integridad DNI {dni}: {e}'))
                    errors += 1
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f'Error inesperado DNI {dni}: {e}'))
                    errors += 1

        self.stdout.write(self.style.SUCCESS('\n=== RESUMEN ==='))
        self.stdout.write(f'Total: {total}')
        self.stdout.write(f'Creados: {created}')
        self.stdout.write(f'Actualizados: {updated}')
        self.stdout.write(f'Omitidos: {skipped}')
        self.stdout.write(f'Errores: {errors}')
        if dry_run:
            self.stdout.write(self.style.WARNING('--- DRY RUN: Sin cambios reales ---'))