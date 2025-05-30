from django.apps import AppConfig


class FirebaseAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "firebase_app"
    
    def ready(self):
        import firebase_app.signals