from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from utils.decorators import role_required
from utils.constants import Roles
from models import db, UploadedFile
from werkzeug.utils import secure_filename
import os
import uuid
from flask_wtf import FlaskForm
from wtforms import StringField, FileField
from wtforms.validators import DataRequired, Length
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mimetypes import guess_type

files_bp = Blueprint('files', __name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'jpg', 'png', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class FileUploadForm(FlaskForm):
    file = FileField('File', validators=[DataRequired()])
    folder = StringField('Folder', validators=[Length(max=100)])
    tags = StringField('Tags', validators=[Length(max=200)])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@files_bp.route('/files/upload', methods=['GET', 'POST'])
@role_required([Roles.SUPER_HQ])
def upload_file():
    form = FileUploadForm()
    if form.validate_on_submit():
        file = form.file.data
        folder = form.folder.data.strip() or 'default'
        tags = form.tags.data.strip()
        if not allowed_file(file.filename):
            flash('File type not allowed.', 'danger')
            return redirect(url_for('files.upload_file'))
        filename = secure_filename(file.filename)
        folder_path = os.path.join(UPLOAD_FOLDER, folder)
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, filename)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            flash('File exceeds maximum size.', 'danger')
            return redirect(url_for('files.upload_file'))
        file.save(file_path)
        uploaded = UploadedFile(filename=filename, folder=folder, tags=tags, path=file_path, uploaded_by=session.get('user'))
        db.session.add(uploaded)
        db.session.commit()
        flash('File uploaded successfully!', 'success')
        return redirect(url_for('files.upload_file'))
    return render_template('files/upload.html', form=form)

@files_bp.route('/folders/create', methods=['POST'])
@role_required([Roles.SUPER_HQ])
def create_folder():
    folder = request.form.get('folder', '').strip()
    if not folder:
        flash('Folder name is required.', 'danger')
        return redirect(url_for('files.upload_file'))
    folder_path = os.path.join(UPLOAD_FOLDER, folder)
    try:
        os.makedirs(folder_path, exist_ok=False)
        flash('Folder created successfully!', 'success')
    except FileExistsError:
        flash('Folder already exists.', 'warning')
    except Exception as e:
        flash(f'Error creating folder: {str(e)}', 'danger')
    return redirect(url_for('files.upload_file'))

@files_bp.route('/files/search', methods=['GET'])
@role_required([Roles.SUPER_HQ])
def search_files():
    query = request.args.get('q', '').strip()
    folder = request.args.get('folder', '').strip()
    tags = request.args.get('tags', '').strip()
    files_query = UploadedFile.query
    if query:
        files_query = files_query.filter(UploadedFile.filename.ilike(f'%{query}%'))
    if folder:
        files_query = files_query.filter(UploadedFile.folder == folder)
    if tags:
        files_query = files_query.filter(UploadedFile.tags.ilike(f'%{tags}%'))
    files = files_query.order_by(UploadedFile.uploaded_at.desc()).all()
    return render_template('files/search.html', files=files, query=query, folder=folder, tags=tags)

@files_bp.route('/files/<int:file_id>', methods=['GET', 'POST', 'DELETE'])
@role_required([Roles.SUPER_HQ])
def file_detail(file_id):
    file_record = UploadedFile.query.get_or_404(file_id)
    if request.method == 'POST':
        tags = request.form.get('tags', '').strip()
        if tags:
            file_record.tags = tags
            db.session.commit()
            flash('Tags updated!', 'success')
        return redirect(url_for('files.file_detail', file_id=file_id))
    elif request.method == 'DELETE':
        try:
            os.remove(file_record.path)
        except Exception:
            pass  # Ignore file not found
        db.session.delete(file_record)
        db.session.commit()
        flash('File deleted!', 'success')
        return redirect(url_for('files.search_files'))
    return render_template('files/detail.html', file=file_record)
