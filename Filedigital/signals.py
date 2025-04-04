from django.db.models.signals import post_save
from django.dispatch import receiver
from  firebase_app.firebase import generate_firebase_auth_key, send_push_notification
from firebase_app. models import *
from firebase_app. serializers import *

@receiver(post_save, sender=File)
def create_notification_token(sender, instance, created, **kwargs):
   print("Signal triggered.")
   if created:
         owner = instance.file_uploaded_by
         auth_token = generate_firebase_auth_key()
         print("auth_token:",auth_token)
         try:
            notification_token, created = NotificationToken.objects.get_or_create(owner=owner, token = auth_token)
            print("Notification token created:",notification_token)
            fcm_token = FCMTokens.objects.first().fcm_token
            if created:
               # notification_token.token = generate_firebase_auth_key()
               notification_token.save()
               send_push_notification(notification_token.token,fcm_token)
               # trigger_notification(owner,"Testing", "message testing")
         except Exception as e:
            print(f"Error creating notification token: {e}")
