from django.conf import settings
from django.core.management import BaseCommand
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = 'Try add all default files, configure DEFAULT_FILE_ADDERS in settings'

    def handle(self, *args, **options):
        for file_adder in settings.DEFAULT_FILE_ADDERS:
            file_adder_func = import_string(file_adder)
            try:
                file_adder_func()
            except Exception as e:
                print('add default file error:', e)
