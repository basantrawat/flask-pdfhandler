import os
from flask import Blueprint, request, render_template, jsonify, url_for, send_from_directory, current_app, session
from werkzeug.utils import secure_filename
from app.utils import (
    allowed_file, generate_unique_filename, merge_pdfs, compress_pdf,
    convert_pdf_to_jpg, split_pdf, rotate_pdf, add_page_numbers,
    watermark_pdf, unlock_pdf, convert_pdf_to_word, generate_unique_folder_name
)

bp = Blueprint('main', __name__)

# Page routes
@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/new')
def new_homepage():
    return render_template('index-new.html')

@bp.route('/<tool_name>')
def tool_page(tool_name):
    valid_tools = [
        'merge', 'compress', 'pdf-to-jpg', 'split', 'rotate',
        'add-page-numbers', 'add-watermark', 'unlock-pdf', 'pdf-to-word'
    ]
    if tool_name in valid_tools:
        return render_template(f'{tool_name}.html')
    else:
        return "Tool not found", 404

# API route for file uploads and processing
@bp.route('/api/upload/<tool>/', methods=['POST'])
def upload_file(tool):
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    files = request.files.getlist('files')
    saved_paths = []

    os.makedirs(os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER']), exist_ok=True)
    
    for file in files:
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid or no file selected'}), 400
        filename = secure_filename(file.filename)

        base, ext = os.path.splitext(filename)
        unique_random_string = generate_unique_folder_name()
        new_fname = f"{base}_{unique_random_string}{ext}"

        filepath = os.path.join(current_app.root_path, '..', current_app.config['UPLOAD_FOLDER'], new_fname)
        
        file.save(filepath)
        saved_paths.append(filepath)

    try:
        if tool == 'merge':
            if len(saved_paths) < 2:
                raise ValueError('Merge requires at least two files.')
            result_filename = merge_pdfs(saved_paths)

        elif tool == 'split':
            if len(saved_paths) != 1:
                raise ValueError('Split requires exactly one file.')
            range_string = request.form.get('ranges')
            if not range_string:
                raise ValueError('Page ranges are required for splitting.')
            result_filename = split_pdf(saved_paths[0], range_string)
        
        elif tool == 'compress':
            if len(saved_paths) != 1:
                raise ValueError('Compress requires exactly one file.')
            result_filename = compress_pdf(saved_paths[0])

        elif tool == 'rotate':
            if len(saved_paths) != 1:
                raise ValueError('Rotate requires exactly one file.')
            angle = int(request.form.get('angle', 90))
            result_filename = rotate_pdf(saved_paths[0], angle)

        elif tool == 'add-page-numbers':
            if len(saved_paths) != 1:
                raise ValueError('This tool requires exactly one file.')
            result_filename = add_page_numbers(saved_paths[0])

        elif tool == 'add-watermark':
            if len(saved_paths) != 1:
                raise ValueError('Watermark requires exactly one file.')
            text = request.form.get('text')
            if not text:
                raise ValueError('Watermark text is required.')
            result_filename = watermark_pdf(saved_paths[0], text)

        elif tool == 'unlock-pdf':
            if len(saved_paths) != 1:
                raise ValueError('Unlock requires exactly one file.')
            password = request.form.get('password', '')
            result_filename = unlock_pdf(saved_paths[0], password)

        elif tool == 'pdf-to-word':
            if len(saved_paths) != 1:
                raise ValueError('PDF to Word requires exactly one file.')
            result_filename = convert_pdf_to_word(saved_paths[0])

        elif tool == 'pdf-to-jpg':
            if len(saved_paths) != 1:
                raise ValueError('PDF to JPG requires exactly one file.')
            result_filename = convert_pdf_to_jpg(saved_paths[0])
        else:
            return jsonify({'error': 'Invalid tool selected.'}), 400

        download_url = url_for('main.download_file', filename=result_filename)
        return jsonify({'download_url': download_url, 'filename': result_filename})

    except Exception as e:
        print(f"An error occurred during {tool} processing: {e}")
        return jsonify({'error': str(e)}), 500

    finally:
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)

@bp.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(os.path.join(current_app.root_path, '..', current_app.config['PROCESSED_FOLDER']), filename, as_attachment=True)
