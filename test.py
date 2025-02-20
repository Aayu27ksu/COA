import fitz  # PyMuPDF for PDF text extraction
from pdf2image import convert_from_path
import pytesseract
import json
from google import genai  # Corrected Gemini import
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io

# Configure Gemini AI
api_key = "AIzaSyD1mBhbd3F6Wsm47tvs86fdzXeMdlJ1xJY"  # Replace with your actual API Key
client = genai.Client(api_key=api_key)
model_id = "gemini-2.0-flash"  # or another valid model ID


# Function to extract text from PDF (with fallback to OCR if necessary)
def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        extracted_text = "\n".join([page.get_text("text") for page in doc])

        if not extracted_text.strip():  # If no text found, try OCR
            print("No text found, attempting OCR...")
            extracted_text = extract_text_from_pdf_with_ocr(file_path)

        return extracted_text.strip()
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""


# Function to perform OCR on scanned PDFs
def extract_text_from_pdf_with_ocr(file_path):
    try:
        images = convert_from_path(file_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        print(f"Error extracting text using OCR: {e}")
        return ""


# Function to process extracted text with Gemini AI
def process_text_with_gemini(extracted_text):
    prompt = f"Extract structured Certificate of Analysis (COA) data from the following text:\n{extracted_text}\nProvide data in JSON format."
    try:
        response = client.completions.create(
            model=model_id,
            prompt=prompt,
            max_tokens=500
        )

        structured_data = json.loads(response['choices'][0]['text'].strip()) if 'choices' in response else {}
        return structured_data
    except json.JSONDecodeError:
        print("Error parsing Gemini response. Check the format.")
        return {}
    except Exception as e:
        print(f"Error processing text with Gemini: {e}")
        return {}


# Function to determine approval status
def check_status(value, min_val, max_val):
    try:
        value, min_val, max_val = float(value), float(min_val), float(max_val)
        return "✅ Approved" if min_val <= value <= max_val else "❌ Rejected"
    except ValueError:
        return "❌ Data Error"


# Function to add watermark to a PDF
def add_watermark(input_pdf_path, output_pdf_path, status_list):
    watermark_text = "APPROVED" if all(status == "✅ Approved" for status in status_list) else "REJECTED"

    pdf_reader = PdfReader(input_pdf_path)
    pdf_writer = PdfWriter()

    # Create watermark
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 60)
    can.setFillColor(colors.green if watermark_text == "APPROVED" else colors.red)
    can.translate(letter[0] / 2, letter[1] / 2)
    can.rotate(45)
    can.drawCentredString(0, 0, watermark_text)
    can.save()

    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]

    # Apply watermark to each page
    for page in pdf_reader.pages:
        page.merge_page(watermark_page)  # Corrected method
        pdf_writer.add_page(page)

    with open(output_pdf_path, "wb") as output_pdf:
        pdf_writer.write(output_pdf)

    print(f"Watermarked PDF generated successfully: {output_pdf_path}")


# Example usage
pdf_path = r"C:\Users\ayush\PycharmProjects\COA\O121 1975-3249 4500724479.pdf"
extracted_text = extract_text_from_pdf(pdf_path)

if extracted_text.strip():  # Check if extracted text is not just whitespace
    structured_data = process_text_with_gemini(extracted_text)

    # Extract relevant data for watermarking
    if structured_data:
        status_list = [
            check_status(
                structured_data.get("inherent_viscosity", 0),
                structured_data.get("inherent_viscosity_min", 0),
                structured_data.get("inherent_viscosity_max", 0)
            )
        ]

        # Add watermark based on extracted data
        add_watermark(pdf_path, "output_with_watermark.pdf", status_list)
    else:
        print("No structured data extracted. Skipping watermarking.")
else:
    print("No meaningful text extracted from PDF.")
