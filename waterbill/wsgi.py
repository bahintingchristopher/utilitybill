import os
import sys

# The path to your project
path = '/home/utilitybill'
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'waterbill.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()