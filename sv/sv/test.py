import sys

import django
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.append(base_dir)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sv.settings')
django.setup()


def main():
    """ test code
    """
    pass


if __name__ == "__main__":
    main()
