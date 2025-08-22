from django.http import HttpResponse
from django.conf import settings
import os

def email_debug_view(request):
    """
    Simple debug view to check email configuration.
    Access via: /sms/email-debug/
    """
    debug_info = []
    
    # Environment detection
    debug_info.append("=== ENVIRONMENT DETECTION ===")
    debug_info.append(f"IS_PRODUCTION (raw): '{os.getenv('IS_PRODUCTION', 'NOT SET')}'")
    debug_info.append(f"ON_PYTHONANYWHERE: {getattr(settings, 'ON_PYTHONANYWHERE', 'NOT SET')}")
    debug_info.append(f"DEBUG: {getattr(settings, 'DEBUG', 'NOT SET')}")
    
    # Email settings
    debug_info.append("\n=== EMAIL SETTINGS ===")
    debug_info.append(f"SMS_NOTIFICATION_EMAIL_1: {getattr(settings, 'SMS_NOTIFICATION_EMAIL_1', 'NOT SET')}")
    debug_info.append(f"SMS_NOTIFICATION_EMAIL_2: {getattr(settings, 'SMS_NOTIFICATION_EMAIL_2', 'NOT SET')}")
    debug_info.append(f"DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')}")
    
    # Environment variables (the source)
    debug_info.append("\n=== ENVIRONMENT VARIABLES ===")
    debug_info.append(f"DIRECTOR_EMAIL: {os.getenv('DIRECTOR_EMAIL', 'NOT SET')}")
    debug_info.append(f"SMS_MANAGER_EMAIL: {os.getenv('SMS_MANAGER_EMAIL', 'NOT SET')}")
    debug_info.append(f"DEV_RECEIVER_EMAIL: {os.getenv('DEV_RECEIVER_EMAIL', 'NOT SET')}")
    debug_info.append(f"EMAIL_USER: {os.getenv('EMAIL_USER', 'NOT SET')}")
    
    # Path info
    debug_info.append("\n=== PATH INFO ===")
    debug_info.append(f"Current working directory: {os.getcwd()}")
    
    # Check if .env file exists
    possible_env_paths = [
        '.env',
        '../.env',
        '../../.env',
        '/home/yourusername/.env',  # Replace with actual username
    ]
    
    debug_info.append("\n=== .ENV FILE CHECK ===")
    for path in possible_env_paths:
        try:
            if os.path.exists(path):
                debug_info.append(f"✅ Found: {path}")
            else:
                debug_info.append(f"❌ Not found: {path}")
        except:
            debug_info.append(f"❌ Error checking: {path}")
    
    html_content = f"<pre>{'<br>'.join(debug_info)}</pre>"
    return HttpResponse(html_content)
