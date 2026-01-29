import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from apps.notifications.models import UserDevice
import os
import json
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase App
try:
    # Check for credentials in environment variable
    cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
    cred_json = os.environ.get('FIREBASE_CONFIG_JSON')
    
    cred = None
    if cred_path and os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
    elif cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
        
    if cred:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
    else:
        logger.warning("Firebase credentials not found. Push notifications will not work.")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")

def send_push_via_fcm(tokens, title, body, data=None):
    """
    Sends multicast message via FCM.
    Handles token cleanup for invalid tokens.
    """
    if not tokens:
        return
    # or not firebase_admin._apps: removed for testing mock purposes, as mock patches library calls


    # Convert data values to strings (FCM requirement)
    str_data = {k: str(v) for k, v in data.items()} if data else {}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body
        ),
        data=str_data,
        tokens=tokens,
    )

    try:
        # firebase_admin.messaging.send_multicast is the function
        # But we need to check if it's available in this version
        # If not, use send_each_for_multicast
        if hasattr(messaging, 'send_multicast'):
            response = messaging.send_multicast(message)
        else:
            response = messaging.send_each_for_multicast(message)
        
        if response.failure_count > 0:
            responses = response.responses
            failed_tokens = []
            for idx, resp in enumerate(responses):
                if not resp.success:
                    # The order of responses corresponds to the order of the registration tokens.
                    failed_tokens.append(tokens[idx])
                    
                    # Check if error is due to invalid token
                    # Common errors: 'registration-token-not-registered', 'invalid-registration-token'
                    err_code = resp.exception.code
                    if err_code == 'NOT_FOUND' or isinstance(resp.exception, messaging.UnregisteredError) or str(resp.exception) == 'Requested entity was not found.':
                         # Mark device as inactive
                         UserDevice.objects.filter(token=tokens[idx]).update(is_active=False)
                         logger.info(f"Invalidated token: {tokens[idx]}")
                    else:
                        logger.warning(f"FCM Send Error for token {tokens[idx]}: {resp.exception}")

    except Exception as e:
        logger.error(f"Critical error sending FCM multicast: {e}")

def notify_user_push(user, title, body, data=None):
    """
    Sends push notification to all active devices of a user.
    Non-blocking / Safe wrapper.
    """
    try:
        devices = UserDevice.objects.filter(user=user, is_active=True)
        tokens = list(devices.values_list('token', flat=True))
        
        if tokens:
            send_push_via_fcm(tokens, title, body, data)
            
    except Exception as e:
        logger.error(f"Failed to notify user {user.id}: {e}")
