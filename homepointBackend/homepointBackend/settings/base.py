# base.py
from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_collected'

STATICFILES_DIRS = [
    BASE_DIR / 'static',  
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'