"""ASGI config for menu_project.

It exposes the ASGI callable as a module-level variable named ``application``.

See https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/ for more details.
"""

import os

from django.core.asgi import get_asgi_application  # type: ignore

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'menu_project.settings')

application = get_asgi_application()
