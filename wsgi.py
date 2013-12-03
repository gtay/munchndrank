from django.core.wsgi import get_wsgi_application
from dh_static import Cling

application = Cling(get_wsgi_application())