from google import genai
from pydantic import BaseModel, Field
from typing import List
from tabulate import tabulate
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io

# Configure API Key
api_key = "AIzaSyD1mBhbd3F6Wsm47tvs86fdzXeMdlJ1xJY"  # Replace with your actual API Key
client = genai.Client(api_key=api_key)
model_id =  "gemini-2.0-flash"  # or another valid model ID

# Function to upload PDF and get file size (tokens)
def upload_pdf_and_get_file_size(file_path):
    COA_pdf = client.files.upload(file=file_path)
    file_size = client.models.count_tokens(model=model_id, contents=COA_pdf)
    print(f'File: {COA_pdf.display_name} equals to {file_size.total_tokens} tokens')
    return COA_pdf

# Upload PDF and get file size
COA_pdf = upload_pdf_and_get_file_size("coa_mannington_carpets.pdf")

# Function to extract structured data from COA PDF
def extract_structured_data(file_path: str, model: BaseModel):
    file = client.files.upload(file=file_path)

    prompt = "Extract the structured Certificate of Analysis (COA) data from this PDF."

    response = client.models.generate_content(model=model_id, contents=[prompt, file], config={'response_mime_type': 'application/json', 'response_schema': model})

    return response.parsed

class COAData(BaseModel):
    # Define all fields as before
    batch_number: str
    net_weight: float
    gross_weight: float
    tare_weight: float
    inherent_viscosity: float
    inherent_viscosity_min: float
    inherent_viscosity_max: float
    volatiles: float
    volatiles_min: float
    volatiles_max: float
    RVCM: float
    RVCM_min: float
    RVCM_max: float
    retained_on_40_mesh: float
    retained_on_40_mesh_min: float
    retained_on_40_mesh_max: float
    retained_on_60_mesh: float
    retained_on_60_mesh_min: float
    retained_on_60_mesh_max: float
    retained_on_80_mesh: float
    retained_on_80_mesh_min: float
    retained_on_80_mesh_max: float
    retained_on_100_mesh: float
    retained_on_100_mesh_min: float
    retained_on_100_mesh_max: float
    retained_on_140_mesh: float
    retained_on_140_mesh_min: float
    retained_on_140_mesh_max: float
    retained_on_200_mesh: float
    retained_on_200_mesh_min: float
    retained_on_200_mesh_max: float
    retained_on_pan: float
    retained_on_pan_min: float
    retained_on_pan_max: float
    DIDP_total_FE_3_min: float
    DIDP_total_FE_3_min_min: float
    DIDP_total_FE_3_min_max: float
    ABD: float
    ABD_min: float
    ABD_max: float
    contamination: int
    contamination_min: int
    contamination_max: int

# Extract structured data from PDF
result = extract_structured_data("coa_mannington_carpets.pdf", COAData)

# Function to check if a value is within range
def check_status(value, min_val, max_val):
    if value is None or min_val is None or max_val is None:
        return "❌ Invalid Data"

    try:
        value, min_val, max_val = float(value), float(min_val), float(max_val)
    except ValueError:
        return "❌ Data Error"

    return "✅ Approved" if min_val <= value <= max_val else "❌ Rejected"


# Prepare the data
data = [
    ["Characteristic", "Unit", "Value", "Min", "Max", "Status"],
    ["Inherent Viscosity", "", result.inherent_viscosity, result.inherent_viscosity_min, result.inherent_viscosity_max,
     check_status(result.inherent_viscosity, result.inherent_viscosity_min, result.inherent_viscosity_max)],
    ["Volatiles", "%", result.volatiles, result.volatiles_min, result.volatiles_max,
     check_status(result.volatiles, result.volatiles_min, result.volatiles_max)],
    ["RVCM", "ppm", result.RVCM, result.RVCM_min, result.RVCM_max,
     check_status(result.RVCM, result.RVCM_min, result.RVCM_max)],
    ["Retained on 40 Mesh", "%", result.retained_on_40_mesh, result.retained_on_40_mesh_min, result.retained_on_40_mesh_max,
     check_status(result.retained_on_40_mesh, result.retained_on_40_mesh_min, result.retained_on_40_mesh_max)],
    ["Retained on 60 Mesh", "%", result.retained_on_60_mesh, result.retained_on_60_mesh_min, result.retained_on_60_mesh_max,
     check_status(result.retained_on_60_mesh, result.retained_on_60_mesh_min, result.retained_on_60_mesh_max)],
    ["Retained on 80 Mesh", "%", result.retained_on_80_mesh, result.retained_on_80_mesh_min, result.retained_on_80_mesh_max,
     check_status(result.retained_on_80_mesh, result.retained_on_80_mesh_min, result.retained_on_80_mesh_max)],
    ["Retained on 100 Mesh", "%", result.retained_on_100_mesh, result.retained_on_100_mesh_min, result.retained_on_100_mesh_max,
     check_status(result.retained_on_100_mesh, result.retained_on_100_mesh_min, result.retained_on_100_mesh_max)],
    ["Retained on 140 Mesh", "%", result.retained_on_140_mesh, result.retained_on_140_mesh_min, result.retained_on_140_mesh_max,
     check_status(result.retained_on_140_mesh, result.retained_on_140_mesh_min, result.retained_on_140_mesh_max)],
    ["Retained on 200 Mesh", "%", result.retained_on_200_mesh, result.retained_on_200_mesh_min, result.retained_on_200_mesh_max,
     check_status(result.retained_on_200_mesh, result.retained_on_200_mesh_min, result.retained_on_200_mesh_max)],
    ["Retained on Pan", "%", result.retained_on_pan, result.retained_on_pan_min, result.retained_on_pan_max,
     check_status(result.retained_on_pan, result.retained_on_pan_min, result.retained_on_pan_max)],
    ["DIDP Total FE (3 Min)", "", result.DIDP_total_FE_3_min, result.DIDP_total_FE_3_min_min, result.DIDP_total_FE_3_min_max,
     check_status(result.DIDP_total_FE_3_min, result.DIDP_total_FE_3_min_min, result.DIDP_total_FE_3_min_max)],
    ["ABD", "g/cc", result.ABD, result.ABD_min, result.ABD_max,
     check_status(result.ABD, result.ABD_min, result.ABD_max)],
    ["Contamination", "", result.contamination, result.contamination_min, result.contamination_max,
     check_status(result.contamination, result.contamination_min, result.contamination_max)]
]

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
add_watermark("coa_mannington_carpets.pdf", "output_with_watermark8.pdf", status_list)
