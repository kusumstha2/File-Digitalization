import pytesseract
from PIL import Image
import pdf2image
from .models import OCRData

def run_ocr(file_instance):
    """Runs OCR on an uploaded file (image or PDF) and stores extracted text."""
    try:
        image_path = file_instance.file.path

        # Check if OCRData already exists for this file
        ocr_entry, created = OCRData.objects.get_or_create(file=file_instance)

        # Check if the file is an image
        if file_instance.file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
            image = Image.open(image_path)
            extracted_text = pytesseract.image_to_string(image)

        # If the file is a PDF, convert it to images and then extract text
        elif file_instance.file.name.lower().endswith('.pdf'):
            images = pdf2image.convert_from_path(image_path)
            extracted_text = "\n".join([pytesseract.image_to_string(img) for img in images])

        else:
            extracted_text = "Unsupported file type for OCR"

        # Update the OCRData entry
        ocr_entry.extracted_text = extracted_text
        ocr_entry.save()

    except Exception as e:
        print(f"Error during OCR processing: {e}")
        ocr_entry.extracted_text = "OCR processing failed"
        ocr_entry.save()


from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials

from firebase_app.models import NotificationToken  # Import your model that stores FCM tokens

def send_notification(user, file_name):
    """Sends an FCM notification to a user."""
    try:
        # Retrieve the FCM token from NotificationToken model
        token_entry = NotificationToken.objects.filter(owner=user).first()
        
        if not token_entry or not token_entry.token:
            print(f"User {user.email} does not have a valid FCM token.")
            return

        message = messaging.Message(
            notification=messaging.Notification(
                title="New Document Uploaded",
                body=f"A new document '{file_name}' has been uploaded."
            ),
            token=token_entry.token  # Get the token from NotificationToken model
        )

        response = messaging.send(message)
        print(f"Notification sent successfully to {user.email}: {response}")

    except messaging.FirebaseError as e:
        print(f"Error sending notification to {user.email}: {e}")
