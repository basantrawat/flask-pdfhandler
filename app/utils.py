import os
import io
import uuid
import zipfile
import subprocess
from pypdf import PdfWriter, PdfReader
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pdf2docx import Converter
import datetime
import random
from flask import current_app


ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(extension):
    return f"{uuid.uuid4()}.{extension}"

def parse_page_ranges(range_string, max_pages):
    pages_to_process = set()
    parts = range_string.replace(" ", "").split(',')
    for part in parts:
        if not part:
            continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end or start < 1 or end > max_pages:
                    raise ValueError("Invalid page range.")
                pages_to_process.update(range(start - 1, end))
            except ValueError:
                raise ValueError(f"Invalid range format: {part}")
        else:
            try:
                page_num = int(part)
                if page_num < 1 or page_num > max_pages:
                    raise ValueError(f"Page number {page_num} is out of bounds.")
                pages_to_process.add(page_num - 1)
            except ValueError:
                raise ValueError(f"Invalid page number: {part}")
    return sorted(list(pages_to_process))

def merge_pdfs(file_paths):
    merger = PdfWriter()
    for pdf_path in file_paths:
        merger.append(pdf_path)
    output_filename = generate_unique_filename('pdf')
    output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
    merger.write(output_path)
    merger.close()
    return output_filename

def compress_pdf(input_file, quality="/ebook"):
    output_filename = generate_unique_filename('pdf')
    output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)
    subprocess.run([
        "gswin64c", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS={quality}",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        f"-sOutputFile={output_path}", input_file
    ])
    return output_filename

def convert_pdf_to_jpg(file_path):
    doc = fitz.open(file_path)
    temp_img_folder_name = str(uuid.uuid4())
    temp_img_folder_path = os.path.join(current_app.config['PROCESSED_FOLDER'], temp_img_folder_name)
    os.makedirs(temp_img_folder_path, exist_ok=True)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        pix.save(os.path.join(temp_img_folder_path, f"page_{page_num + 1}.jpg"))
    doc.close()
    zip_filename = generate_unique_filename('zip')
    zip_path = os.path.join(current_app.config['PROCESSED_FOLDER'], zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(temp_img_folder_path):
            for file in files:
                zipf.write(os.path.join(root, file), file)
    return zip_filename

def split_pdf(file_path, range_string):
    reader = PdfReader(file_path)
    writer = PdfWriter()
    total_pages = len(reader.pages)
    pages_to_extract = parse_page_ranges(range_string, total_pages)
    if not pages_to_extract:
        raise ValueError("No valid pages selected for extraction.")
    for page_index in pages_to_extract:
        writer.add_page(reader.pages[page_index])
    output_filename = generate_unique_filename('pdf')
    output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_filename

def rotate_pdf(file_path, angle):
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    output_filename = generate_unique_filename('pdf')
    output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_filename

def add_page_numbers(file_path):
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for i, page in enumerate(reader.pages):
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.drawString(letter[0] / 2, 30, str(i + 1))  # Position the number at bottom center
        can.save()
        packet.seek(0)
        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]
        page.merge_page(watermark_page)
        writer.add_page(page)
    output_filename = generate_unique_filename('pdf')
    output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_filename

def watermark_pdf(file_path, text):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica", 40)
    can.setFillGray(0.5, 0.5)  # gray with 50% transparency
    can.saveState()
    can.translate(300, 400)  # move to center
    can.rotate(45)  # rotate text diagonally
    can.drawCentredString(0, 0, text)
    can.restoreState()
    can.save()
    packet.seek(0)
    watermark_reader = PdfReader(packet)
    watermark_page = watermark_reader.pages[0]
    reader = PdfReader(file_path)
    writer = PdfWriter()
    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)
    output_filename = generate_unique_filename('pdf')
    output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
    with open(output_path, "wb") as f:
        writer.write(f)
    return output_filename

def unlock_pdf(file_path, password):
    reader = PdfReader(file_path)
    if not reader.is_encrypted:
        raise ValueError("The provided PDF file is not encrypted.")
    if reader.decrypt(password):
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        output_filename = generate_unique_filename('pdf')
        output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
        with open(output_path, "wb") as f:
            writer.write(f)
        return output_filename
    else:
        raise ValueError("Incorrect password provided. Decryption failed.")

def convert_pdf_to_word(file_path):
    output_filename = generate_unique_filename('docx')
    output_path = os.path.join(current_app.config['PROCESSED_FOLDER'], output_filename)
    cv = Converter(file_path)
    cv.convert(output_path, start=0)
    cv.close()
    return output_filename

def generate_unique_folder_name():
    """
    Generate a unique folder name using current time + random number.

    Format: yyyymmddhhmmss_<randomnumber>
    e.g. 250908143025_839271
    """
    timestamp = datetime.datetime.now().strftime('%y%m%d%H%M%S')
    rand_num = random.randint(100, 999)  # 4-digit random number
    folder_name = f"{timestamp}_{rand_num}"

    return folder_name