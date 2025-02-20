from google import genai
from pydantic import BaseModel, create_model
from typing import List, Dict, Any
from tabulate import tabulate
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io

# Configure API Key
api_key = "AIzaSyD1mBhbd3F6Wsm47tvs86fdzXeMdlJ1xJY"  # Replace with your actual API Key
client = genai.Client(api_key=api_key)
model_id = "gemini-2.0-flash"  # or another valid model ID

# Function to upload PDF and get file size (tokens)
def upload_pdf_and_get_file_size(file_path):
    COA_pdf = client.files.upload(file=file_path)
    file_size = client.models.count_tokens(model=model_id, contents=COA_pdf)
    print(f'File: {COA_pdf.display_name} equals to {file_size.total_tokens} tokens')
    return COA_pdf

# Get file path from user input
file_path = input("Please enter the path to the PDF file: ")

# Upload PDF and get file size
uploaded_pdf = upload_pdf_and_get_file_size(file_path)
uploaded_pdf_name = uploaded_pdf.display_name

# Function to extract structured data from COA PDF
def extract_structured_data(file):
    prompt = "Extract the structured Certificate of Analysis (COA) data from this PDF."
    response = client.models.generate_content(model=model_id, contents=[prompt, file], config={'response_mime_type': 'application/json'})
    return response.parsed

# Extract structured data from PDF
extracted_data = extract_structured_data(uploaded_pdf)

# Check if extracted data is valid
if not extracted_data:
    raise ValueError("Failed to extract data from the PDF.")

# Function to dynamically create a Pydantic model based on extracted data
def create_dynamic_model(data: Dict[str, Any]) -> BaseModel:
    fields = {key: (type(value), ...) for key, value in data.items()}
    return create_model('DynamicCOAData', **fields)

# Create dynamic model based on extracted data
DynamicCOAData = create_dynamic_model(extracted_data)

# Parse extracted data into the dynamic model
result = DynamicCOAData(**extracted_data)

# Function to check if a value is within range
def check_status(value, min_val, max_val):
    if value is None or min_val is None or max_val is None:
        return "❌ Invalid Data"

    try:
        value, min_val, max_val = float(value), float(min_val), float(max_val)
    except ValueError:
        return "❌ Data Error"

    return "✅ Approved" if min_val <= value <= max_val else "❌ Rejected"

# Prepare the data dynamically
data = [["Characteristic", "Unit", "Value", "Min", "Max", "Status"]]
for field in result.__fields__:
    if field.endswith('_min') or field.endswith('_max'):
        continue
    value = getattr(result, field)
    min_val = getattr(result, f"{field}_min", None)
    max_val = getattr(result, f"{field}_max", None)
    status = check_status(value, min_val, max_val)
    data.append([field.replace('_', ' ').title(), "", value, min_val, max_val, status])

# Check if all statuses are approved
all_approved = all(row[5] == "✅ Approved" for row in data[1:])

# Determine watermark text based on status
watermark_text = "APPROVED" if all_approved else "REJECTED"

# Print Table in Console
print(tabulate(data, headers="firstrow", tablefmt="grid"))

# Function to add watermark to original PDF
def determine_watermark_text(status_list):
    return "APPROVED" if all(status.upper() == "APPROVED" for status in status_list) else "REJECTED"

def add_watermark(input_pdf_path, output_pdf_path, status_list):
    print(f"Starting to add watermark to {input_pdf_path}...")

    watermark_text = determine_watermark_text(status_list)

    try:
        pdf_reader = PdfReader(input_pdf_path)
        pdf_writer = PdfWriter()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return

    # Create a watermark PDF in memory
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 60)
    watermark_color = colors.green if watermark_text == "APPROVED" else colors.red
    can.setFillColor(watermark_color)

    # Rotate watermark diagonally
    can.translate(letter[0] / 2, letter[1] / 2)
    can.rotate(45)

    # Draw centered watermark
    can.drawCentredString(0, 0, watermark_text)
    can.save()

    # Move to the beginning of the watermark PDF
    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]

    # Apply the watermark to each page
    for page in pdf_reader.pages:
        page.merge_page(watermark_page)  # Merge watermark
        pdf_writer.add_page(page)

    # Write the final output PDF
    try:
        with open(output_pdf_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)
        print(f"Watermarked PDF generated successfully: {output_pdf_path}")
    except Exception as e:
        print(f"Error saving output PDF: {e}")

# Example usage
status_list = ["APPROVED", "APPROVED", "REJECTED"]  # Example status list
add_watermark(file_path, "output_with_watermark8.pdf", status_list)