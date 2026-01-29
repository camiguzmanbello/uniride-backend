from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone
from apps.users.models import User, Role
from apps.chat.models import Chat, Message
from apps.trips.models import Publication, PublicationType
from apps.notifications.models import Notification, UserDevice
from unittest.mock import patch, MagicMock
from firebase_admin import messaging

class NotificationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role_user = Role.objects.create(name='Usuario')
        self.user1 = User.objects.create_user(username='user1', email='u1@test.com', password='pwd', name='U1', role_id=self.role_user)
        self.user2 = User.objects.create_user(username='user2', email='u2@test.com', password='pwd', name='U2', role_id=self.role_user)
        
        self.type_offer = PublicationType.objects.create(name='Oferta')
        self.pub = Publication.objects.create(
            user_id=self.user1, type_id=self.type_offer,
            departure_place="A", destination="B", departure_datetime=timezone.now(),
            lat_departure_place=0, lon_departure_place=0, lat_destination=0, lon_destination=0
        )
        self.chat = Chat.objects.create(publication=self.pub, driver=self.user1, passenger=self.user2)

    def test_notification_creation_on_message(self):
        """Test that a Notification is created when a Message is saved."""
        self.assertEqual(Notification.objects.count(), 0)
        
        # User 1 sends message to User 2
        msg = Message.objects.create(chat_id=self.chat, sender_id=self.user1, content="Hello")
        
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.recipient, self.user2)
        self.assertEqual(notif.type, 'NEW_CHAT_MESSAGE')
        self.assertIn('Hello', notif.message)
        self.assertEqual(notif.metadata.get('chat_id'), self.chat.id)
        self.assertEqual(notif.metadata.get('message_id'), msg.id)

    @patch('apps.notifications.services.push.messaging.send_each_for_multicast')
    def test_push_dispatch_mock(self, mock_send):
        """Test that firebase send_multicast is called with correct params."""
        # Register device for User 2
        UserDevice.objects.create(user=self.user2, token='token_u2', platform='android')
        
        mock_response = MagicMock()
        mock_response.failure_count = 0
        mock_send.return_value = mock_response
        
        # User 1 sends message
        msg = Message.objects.create(chat_id=self.chat, sender_id=self.user1, content="Push Test")
        
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0][0] # The MulticastMessage object
        self.assertEqual(call_args.tokens, ['token_u2'])
        self.assertEqual(call_args.notification.title, 'Nuevo Mensaje')
        self.assertEqual(call_args.notification.body, 'Push Test')
        self.assertEqual(call_args.data.get('chat_id'), str(self.chat.id))
        self.assertEqual(call_args.data.get('message_id'), str(msg.id))

    @patch('apps.notifications.services.push.messaging.send_each_for_multicast')
    def test_token_cleanup_on_error(self, mock_send):
        """Test that invalid tokens are marked inactive."""
        UserDevice.objects.create(user=self.user2, token='bad_token', platform='android')
        
        # Mock Firebase response with failure
        mock_response = MagicMock()
        mock_response.failure_count = 1
        mock_fail = MagicMock()
        mock_fail.success = False
        mock_fail.exception = messaging.UnregisteredError('Token invalid')
        mock_response.responses = [mock_fail]
        
        mock_send.return_value = mock_response
        
        # Trigger
        Message.objects.create(chat_id=self.chat, sender_id=self.user1, content="Cleanup Test")
        
        # Check DB
        device = UserDevice.objects.get(token='bad_token')
        self.assertFalse(device.is_active)

    def test_security_notifications_isolation(self):
        """Test that user can only see their own notifications."""
        # Create notif for User 1
        Notification.objects.create(recipient=self.user1, type='NEW_CHAT_MESSAGE', title='For U1', message='Msg')
        # Create notif for User 2
        Notification.objects.create(recipient=self.user2, type='NEW_CHAT_MESSAGE', title='For U2', message='Msg')
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/notifications/notifications/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1) # Only 1, not 2
        self.assertEqual(response.data[0]['title'], 'For U1')
