import random
import string
import asyncio
from django.conf import settings
from django.contrib.auth import authenticate, login
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from .telegram_bot import send_admin_access_key
import icecream as ic

class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_key = None
        self.last_regenerate_time = None

    def __call__(self, request):
        if request.path.startswith('/admin/np/'):
            key = request.path.split('/admin/np/')[1].rstrip('/')
            if key == self.admin_key:
                user = authenticate(
                    request,
                    username=settings.ADMIN_AUTO_LOGIN_USERNAME,
                    password=settings.ADMIN_AUTO_LOGIN_PASSWORD
                )
                if user is not None:
                    login(request, user)
                    request.path_info = '/admin/'
                    return self.get_response(request)
                else:
                    return HttpResponseForbidden("Invalid admin credentials")
            else:
                if request.method == 'POST' and request.POST.get('action') == 'regenerate_key':
                    if self.can_regenerate_key():
                        self.generate_and_send_key(request)
                        return HttpResponse("Key regenerated. Check the Telegram channel.")
                    else:
                        return HttpResponseForbidden("You can only request a new key once per minute.")
                return HttpResponseForbidden(self.get_invalid_key_message())
        elif request.path == '/admin/' or request.path == '/admin':
            if settings.DEFAULT_DJANGO_ADMIN_PANEL:
                self.generate_and_send_key(request)
                return self.get_response(request)
            else:
                self.generate_and_send_key(request)
                return HttpResponseForbidden("Access key generated. Check the Telegram channel.")
        return self.get_response(request)

    def get_invalid_key_message(self):
        regenerate_button_html = (
            '<form method="post">'
            '<input type="hidden" name="action" value="regenerate_key">'
            '<button type="submit">Re-generate Key</button>'
            '</form>'
        )
        return f"Invalid admin key. {regenerate_button_html}"

    def can_regenerate_key(self):
        if self.last_regenerate_time is None:
            return True
        now = timezone.now()
        elapsed_time = (now - self.last_regenerate_time).total_seconds()
        return elapsed_time >= 60  # 60 seconds = 1 minute

    def generate_and_send_key(self, request):
        self.admin_key = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        ip = self.get_client_ip(request)
        user_agent = self.get_user_agent(request)
        message = (
            f"Admin key generated.\n"
            f"IP address: `{ip}`\n"
            f"Browser: `{user_agent}`\n"
            f"Key: `{self.admin_key}`"
        )

        if settings.ADMIN_KEY_IN_TERMINAL or settings.DEBUG:
            ic.ic(message)
            print(f"Key generated.\nKey: {self.admin_key}")
        
        if settings.ADMIN_KEY_IN_TELEGRAM:
            try:
                asyncio.run(send_admin_access_key(ip, user_agent, self.admin_key))
            except Exception as e:
                if not settings.ADMIN_KEY_IN_TERMINAL and not settings.DEBUG:
                    print("Admin key generated but failed to send to Telegram.")
                print(f"Error: {e}")

        # Update the last regenerate time
        self.last_regenerate_time = timezone.now()

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def get_user_agent(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        return user_agent