import pytesseract
from PIL import Image
import pdf2image
from .models import OCRData

def run_ocr(file_instance):
    try:
        image_path = file_instance.file.path
        
        # Check if the file is an image
        if file_instance.file.name.endswith(('.jpg', '.jpeg', '.png')):
            image = Image.open(image_path)
            extracted_text = pytesseract.image_to_string(image)
        
        # If the file is a PDF, convert it to images and extract text
        elif file_instance.file.name.endswith('.pdf'):
            images = pdf2image.convert_from_path(image_path)
            extracted_text = ''
            for image in images:
                extracted_text += pytesseract.image_to_string(image)
        
        else:
            extracted_text = "Unsupported file type"
        
        # Store the extracted text in the OCRData model
        OCRData.objects.create(file=file_instance, extracted_text=extracted_text)

    except Exception as e:
        print(f"Error during OCR process: {e}")
        OCRData.objects.create(file=file_instance, extracted_text="OCR failed")
