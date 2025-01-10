# your_project_name/asgi.py
import os
from django.conf import settings
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')

django_asgi_app = get_asgi_application()

# 개발 환경에서는 보안 완화 및 베포 환경에선 보안 강화
if settings.DEBUG:
    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    })
else:
    from channels.security.websocket import AllowedHostsOriginValidator
    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        ),
    })
