'''Settings specific to django-multi-gtfs'''

from django.conf import settings
from os import path

_module_location = path.join(path.dirname(__file__))
VALIDATOR = path.join(_module_location, )
# If you fulfill the requirements, the OpenStreetMap layer is nicer
# https://docs.djangoproject.com/en/dev/ref/contrib/gis/tutorial/#osmgeoadmin
MULTIGTFS_OSMADMIN = getattr(settings, 'MULTIGTFS_OSMADMIN', True)
