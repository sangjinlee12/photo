import os
import zipfile
import shutil
import re
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, abort
from werkzeug.utils import secure_filename
from PIL import Image, ExifTags
import io
import tempfile
from app import app, db
from models import Project, Photo

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_path, max_width=1920, max_height=1080, quality=85):
    """Compress image while preserving EXIF data"""
    try:
        with Image.open(image_path) as img:
            # 원본 EXIF 데이터 보존
            exif_dict = None
            if hasattr(img, '_getexif') and img._getexif() is not None:
                exif_dict = img._getexif()
            
            # 이미지 회전 정보 확인 및 적용
            if exif_dict:
                for tag, value in exif_dict.items():
                    if tag in ExifTags.TAGS:
                        if ExifTags.TAGS[tag] == 'Orientation':
                            if value == 3:
                                img = img.rotate(180, expand=True)
                            elif value == 6:
                                img = img.rotate(270, expand=True)
                            elif value == 8:
                                img = img.rotate(90, expand=True)
                            break
            
            # 크기 조정
            original_width, original_height = img.size
            if original_width > max_width or original_height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # JPEG로 변환하고 압축
            if img.mode in ('RGBA', 'LA', 'P'):
                # 투명도가 있는 이미지는 흰색 배경으로 변환
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 압축된 이미지 저장
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            
    except Exception as e:
        app.logger.error(f"Error compressing image {image_path}: {e}")

def extract_photo_info(filename):
    """Extract photo information from filename"""
    # 파일명에서 확장자 제거
    name_without_ext = os.path.splitext(filename)[0]
    
    # 날짜 패턴 매칭 (YYYY-MM-DD_NN 형식)
    date_pattern = r'(\d{4}-\d{2}-\d{2})_(\d+)'
    match = re.search(date_pattern, name_without_ext)
    
    photo_date = None
    description = None
    
    if match:
        date_str = match.group(1)
        sequence = match.group(2)
        
        try:
            # 날짜 파싱
            photo_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            # 설명 생성
            description = f"{date_str}_{sequence.zfill(2)}"
        except ValueError:
            pass
    
    return photo_date, description

@app.route('/')
def index():
    """Main page showing all projects"""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('index.html', projects=projects)

@app.route('/create_project', methods=['GET', 'POST'])
def create_project():
    """Create a new construction project"""
    if request.method == 'POST':
        project_name = request.form.get('project_name', '').strip()
        address = request.form.get('address', '').strip()
        manager_name = request.form.get('manager_name', '').strip()
        manager_phone = request.form.get('manager_phone', '').strip()
        manager_email = request.form.get('manager_email', '').strip()
        
        if not project_name:
            flash('프로젝트 이름을 입력해주세요.', 'error')
            return render_template('create_project.html')
        
        # Check if project name already exists
        existing_project = Project.query.filter_by(name=project_name).first()
        if existing_project:
            flash('이미 존재하는 프로젝트 이름입니다.', 'error')
            return render_template('create_project.html')
        
        try:
            project = Project(
                name=project_name,
                address=address if address else None,
                manager_name=manager_name if manager_name else None,
                manager_phone=manager_phone if manager_phone else None,
                manager_email=manager_email if manager_email else None
            )
            db.session.add(project)
            db.session.commit()
            
            # Create project directory
            project_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(project.id))
            os.makedirs(project_dir, exist_ok=True)
            
            flash(f'프로젝트 "{project_name}"이 성공적으로 생성되었습니다.', 'success')
            return redirect(url_for('index'))
        
        except Exception as e:
            db.session.rollback()
            flash('프로젝트 생성 중 오류가 발생했습니다.', 'error')
            app.logger.error(f"Error creating project: {e}")
    
    return render_template('create_project.html')

@app.route('/upload_photos/<int:project_id>', methods=['GET', 'POST'])
def upload_photos(project_id):
    """Upload photos to a specific project"""
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        app.logger.debug(f"Upload request received for project {project_id}")
        app.logger.debug(f"Request files: {request.files}")
        
        if 'photos' not in request.files:
            app.logger.error("No 'photos' field in request.files")
            flash('파일이 선택되지 않았습니다.', 'error')
            return redirect(request.url)
        
        # 기본 설명 가져오기
        default_description = request.form.get('default_description', '').strip()
        
        files = request.files.getlist('photos')
        app.logger.debug(f"Found {len(files)} files")
        uploaded_count = 0
        
        # Create project directory if it doesn't exist
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(project_id))
        os.makedirs(project_dir, exist_ok=True)
        
        for file in files:
            app.logger.debug(f"Processing file: {file.filename if file else 'None'}")
            if file and file.filename and allowed_file(file.filename):
                try:
                    app.logger.debug(f"File {file.filename} is valid, processing...")
                    # Secure the filename
                    filename = secure_filename(file.filename)
                    app.logger.debug(f"Secured filename: {filename}")
                    
                    # Generate unique filename if already exists
                    counter = 1
                    name, ext = os.path.splitext(filename)
                    while os.path.exists(os.path.join(project_dir, filename)):
                        filename = f"{name}_{counter}{ext}"
                        counter += 1
                    
                    filepath = os.path.join(project_dir, filename)
                    app.logger.debug(f"Saving to: {filepath}")
                    
                    # Save the file
                    file.save(filepath)
                    app.logger.debug(f"File saved successfully: {filepath}")
                    
                    # 이미지 압축 처리
                    try:
                        compress_image(filepath)
                        app.logger.debug(f"Image compressed: {filepath}")
                    except Exception as e:
                        app.logger.error(f"Error compressing image {filepath}: {e}")
                    
                    # 파일명에서 정보 추출
                    photo_date, description = extract_photo_info(filename)
                    
                    # 파일명에서 추출된 설명이 없으면 기본 설명 사용
                    if not description and default_description:
                        description = default_description
                    
                    # Save to database
                    photo = Photo(
                        project_id=project_id,
                        filename=filename,
                        filepath=filepath,
                        photo_date=photo_date,
                        description=description
                    )
                    db.session.add(photo)
                    uploaded_count += 1
                    app.logger.debug(f"Photo record added to database: {filename} with date: {photo_date}, description: {description}")
                    
                except Exception as e:
                    app.logger.error(f"Error uploading file {file.filename}: {e}")
                    import traceback
                    app.logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
            else:
                app.logger.warning(f"File skipped - file: {file}, filename: {file.filename if file else 'None'}, allowed: {allowed_file(file.filename) if file and file.filename else 'N/A'}")
        
        if uploaded_count > 0:
            db.session.commit()
            flash(f'{uploaded_count}개의 사진이 성공적으로 업로드되었습니다.', 'success')
        else:
            flash('업로드된 사진이 없습니다. 지원되는 형식(PNG, JPG, JPEG, GIF, BMP, WEBP)인지 확인해주세요.', 'error')
        
        return redirect(url_for('view_photos', project_id=project_id))
    
    return render_template('upload_photos.html', project=project)

@app.route('/simple_upload/<int:project_id>')
def simple_upload(project_id):
    """Simple upload page for testing"""
    project = Project.query.get_or_404(project_id)
    return render_template('simple_upload.html', project=project)

@app.route('/view_photos/<int:project_id>')
def view_photos(project_id):
    """View photos for a specific project"""
    project = Project.query.get_or_404(project_id)
    photos = Photo.query.filter_by(project_id=project_id).order_by(Photo.uploaded_at.desc()).all()
    return render_template('view_photos.html', project=project, photos=photos)

@app.route('/download_photo/<int:photo_id>')
def download_photo(photo_id):
    """Download a single photo"""
    photo = Photo.query.get_or_404(photo_id)
    
    if not os.path.exists(photo.filepath):
        flash('파일을 찾을 수 없습니다.', 'error')
        return redirect(url_for('view_photos', project_id=photo.project_id))
    
    return send_file(photo.filepath, as_attachment=True, download_name=photo.filename)

@app.route('/download_all_photos/<int:project_id>')
def download_all_photos(project_id):
    """Download all photos for a project as ZIP file"""
    project = Project.query.get_or_404(project_id)
    photos = Photo.query.filter_by(project_id=project_id).all()
    
    if not photos:
        flash('다운로드할 사진이 없습니다.', 'error')
        return redirect(url_for('view_photos', project_id=project_id))
    
    # Create temporary ZIP file
    temp_dir = tempfile.mkdtemp()
    zip_filename = f"{project.name}_작업사진.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for photo in photos:
                if os.path.exists(photo.filepath):
                    zipf.write(photo.filepath, photo.filename)
        
        return send_file(zip_path, as_attachment=True, download_name=zip_filename, 
                        mimetype='application/zip')
    
    except Exception as e:
        app.logger.error(f"Error creating ZIP file: {e}")
        flash('ZIP 파일 생성 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('view_photos', project_id=project_id))
    
    finally:
        # Cleanup temporary directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    """Delete a single photo"""
    photo = Photo.query.get_or_404(photo_id)
    project_id = photo.project_id
    
    try:
        # Delete file from filesystem
        if os.path.exists(photo.filepath):
            os.remove(photo.filepath)
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        
        flash('사진이 성공적으로 삭제되었습니다.', 'success')
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting photo: {e}")
        flash('사진 삭제 중 오류가 발생했습니다.', 'error')
    
    return redirect(url_for('view_photos', project_id=project_id))

@app.route('/delete_all_photos/<int:project_id>', methods=['POST'])
def delete_all_photos(project_id):
    """Delete all photos for a project"""
    project = Project.query.get_or_404(project_id)
    photos = Photo.query.filter_by(project_id=project_id).all()
    
    try:
        # Delete files from filesystem
        for photo in photos:
            if os.path.exists(photo.filepath):
                os.remove(photo.filepath)
        
        # Delete from database
        Photo.query.filter_by(project_id=project_id).delete()
        db.session.commit()
        
        # Remove project directory if empty
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(project_id))
        if os.path.exists(project_dir) and not os.listdir(project_dir):
            os.rmdir(project_dir)
        
        flash('모든 사진이 성공적으로 삭제되었습니다.', 'success')
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting all photos: {e}")
        flash('사진 삭제 중 오류가 발생했습니다.', 'error')
    
    return redirect(url_for('view_photos', project_id=project_id))

@app.route('/edit_photo/<int:photo_id>', methods=['GET', 'POST'])
def edit_photo(photo_id):
    """Edit photo information"""
    photo = Photo.query.get_or_404(photo_id)
    
    if request.method == 'POST':
        try:
            # Get form data
            filename = request.form.get('filename', '').strip()
            photo_location = request.form.get('photo_location', '').strip()
            photo_date = request.form.get('photo_date', '').strip()
            description = request.form.get('description', '').strip()
            
            # Update filename
            if filename:
                # Add extension if not provided
                if '.' not in filename:
                    old_ext = os.path.splitext(photo.filename)[1]
                    filename += old_ext
                photo.filename = filename
            
            # Update photo information
            photo.photo_location = photo_location if photo_location else None
            photo.description = description if description else None
            
            # Parse and update photo date
            if photo_date:
                try:
                    from datetime import datetime
                    photo.photo_date = datetime.strptime(photo_date, '%Y-%m-%d').date()
                except ValueError:
                    flash('날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)', 'error')
                    return render_template('edit_photo.html', photo=photo)
            else:
                photo.photo_date = None
            
            db.session.commit()
            flash('사진 정보가 성공적으로 수정되었습니다.', 'success')
            
            # AJAX 요청인 경우 JSON 응답
            if request.headers.get('Content-Type') == 'application/x-www-form-urlencoded' and 'XMLHttpRequest' not in request.headers.get('X-Requested-With', ''):
                return redirect(url_for('view_photos', project_id=photo.project_id))
            else:
                return "성공적으로 수정되었습니다."
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error updating photo: {e}")
            flash('사진 정보 수정 중 오류가 발생했습니다.', 'error')
    
    return render_template('edit_photo.html', photo=photo)

@app.route('/batch_edit_photos/<int:project_id>', methods=['POST'])
def batch_edit_photos(project_id):
    """Batch edit multiple photos"""
    try:
        # Get form data
        photo_ids_str = request.form.get('photo_ids', '')
        update_location = 'updateLocation' in request.form
        update_date = 'updateDate' in request.form
        update_description = 'updateDescription' in request.form
        
        new_location = request.form.get('location', '').strip() if update_location else None
        new_date_str = request.form.get('date', '').strip() if update_date else None
        new_description = request.form.get('description', '').strip() if update_description else None
        
        # Parse photo IDs
        if not photo_ids_str:
            flash('수정할 사진을 선택해주세요.', 'error')
            return redirect(url_for('view_photos', project_id=project_id))
        
        photo_ids = [int(id.strip()) for id in photo_ids_str.split(',') if id.strip()]
        
        if not photo_ids:
            flash('유효한 사진을 선택해주세요.', 'error')
            return redirect(url_for('view_photos', project_id=project_id))
        
        # Parse date if provided
        new_date = None
        if new_date_str:
            try:
                from datetime import datetime
                new_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)', 'error')
                return redirect(url_for('view_photos', project_id=project_id))
        
        # Update photos
        updated_count = 0
        for photo_id in photo_ids:
            photo = Photo.query.filter_by(id=photo_id, project_id=project_id).first()
            if photo:
                if update_location:
                    photo.photo_location = new_location
                if update_date:
                    photo.photo_date = new_date
                if update_description:
                    photo.description = new_description
                updated_count += 1
        
        db.session.commit()
        
        if updated_count > 0:
            flash(f'{updated_count}개 사진의 정보가 성공적으로 수정되었습니다.', 'success')
        else:
            flash('수정할 사진을 찾을 수 없습니다.', 'error')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in batch edit: {e}")
        flash('일괄 수정 중 오류가 발생했습니다.', 'error')
    
    return redirect(url_for('view_photos', project_id=project_id))

@app.route('/rename_photo/<int:photo_id>', methods=['POST'])
def rename_photo(photo_id):
    """Rename a photo"""
    photo = Photo.query.get_or_404(photo_id)
    new_name = request.form.get('new_name', '').strip()
    
    if not new_name:
        if request.is_json or request.headers.get('Content-Type') == 'application/x-www-form-urlencoded':
            return jsonify({'success': False, 'error': '새 파일명을 입력해주세요.'}), 400
        flash('새 파일명을 입력해주세요.', 'error')
        return redirect(url_for('view_photos', project_id=photo.project_id))
    
    # Add extension if not provided
    if '.' not in new_name:
        old_ext = os.path.splitext(photo.filename)[1]
        new_name += old_ext
    
    try:
        # Update filename in database
        photo.filename = new_name
        db.session.commit()
        
        if request.is_json or 'XMLHttpRequest' in request.headers.get('X-Requested-With', ''):
            return jsonify({'success': True, 'new_name': new_name})
        
        flash('파일명이 성공적으로 변경되었습니다.', 'success')
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error renaming photo: {e}")
        
        if request.is_json or 'XMLHttpRequest' in request.headers.get('X-Requested-With', ''):
            return jsonify({'success': False, 'error': '파일명 변경 중 오류가 발생했습니다.'}), 500
        
        flash('파일명 변경 중 오류가 발생했습니다.', 'error')
    
    return redirect(url_for('view_photos', project_id=photo.project_id))

@app.route('/batch_rename', methods=['POST'])
def batch_rename():
    """Batch rename photos"""
    photo_ids = request.form.getlist('photo_ids[]')
    new_names = request.form.getlist('new_names[]')
    project_id = request.form.get('project_id')
    
    if not photo_ids or not new_names or len(photo_ids) != len(new_names):
        flash('일괄 변경 중 오류가 발생했습니다.', 'error')
        return redirect(url_for('view_photos', project_id=project_id))
    
    try:
        for photo_id, new_name in zip(photo_ids, new_names):
            photo = Photo.query.get(photo_id)
            if photo:
                # Add extension if not provided
                if '.' not in new_name:
                    old_ext = os.path.splitext(photo.filename)[1]
                    new_name += old_ext
                
                photo.filename = new_name
        
        db.session.commit()
        flash('모든 파일명이 성공적으로 변경되었습니다.', 'success')
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in batch rename: {e}")
        flash('일괄 변경 중 오류가 발생했습니다.', 'error')
    
    return redirect(url_for('view_photos', project_id=project_id))

@app.route('/export_album/<int:project_id>')
def export_album(project_id):
    """Export project photos as construction completion album"""
    project = Project.query.get_or_404(project_id)
    photos = Photo.query.filter_by(project_id=project_id).order_by(Photo.uploaded_at.asc()).all()
    
    if not photos:
        flash('내보낼 사진이 없습니다.', 'error')
        return redirect(url_for('view_photos', project_id=project_id))
    
    # 현재 날짜 추가
    current_date = datetime.now().strftime('%Y년 %m월 %d일')
    
    return render_template('photo_album.html', project=project, photos=photos, current_date=current_date)

@app.route('/delete_project/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    """Delete a project and all its photos"""
    project = Project.query.get_or_404(project_id)
    
    try:
        # Delete all photos and files
        photos = Photo.query.filter_by(project_id=project_id).all()
        for photo in photos:
            if os.path.exists(photo.filepath):
                os.remove(photo.filepath)
        
        # Remove project directory
        project_dir = os.path.join(app.config['UPLOAD_FOLDER'], str(project_id))
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        
        # Delete from database (cascade will handle photos)
        db.session.delete(project)
        db.session.commit()
        
        flash(f'프로젝트 "{project.name}"이 성공적으로 삭제되었습니다.', 'success')
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting project: {e}")
        flash('프로젝트 삭제 중 오류가 발생했습니다.', 'error')
    
    return redirect(url_for('index'))

@app.route('/photo_thumbnail/<int:photo_id>')
def photo_thumbnail(photo_id):
    """Serve photo thumbnails"""
    photo = Photo.query.get_or_404(photo_id)
    
    if not os.path.exists(photo.filepath):
        abort(404)
    
    try:
        # Create thumbnail
        with Image.open(photo.filepath) as img:
            img.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img_io = io.BytesIO()
            img_format = img.format or 'JPEG'
            img.save(img_io, format=img_format)
            img_io.seek(0)
            return send_file(img_io, mimetype=f'image/{img_format.lower()}')
    
    except Exception as e:
        app.logger.error(f"Error creating thumbnail: {e}")
        abort(404)

@app.route('/photo_full/<int:photo_id>')
def photo_full(photo_id):
    """Serve full-size photos"""
    photo = Photo.query.get_or_404(photo_id)
    
    if not os.path.exists(photo.filepath):
        abort(404)
    
    return send_file(photo.filepath)

@app.route('/manage_addresses')
def manage_addresses():
    """현장주소 관리 페이지"""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('manage_addresses.html', projects=projects)

@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    """프로젝트 정보 수정"""
    project = Project.query.get_or_404(project_id)
    
    if request.method == 'POST':
        project_name = request.form.get('project_name', '').strip()
        address = request.form.get('address', '').strip()
        manager_name = request.form.get('manager_name', '').strip()
        manager_phone = request.form.get('manager_phone', '').strip()
        manager_email = request.form.get('manager_email', '').strip()
        
        if not project_name:
            flash('프로젝트 이름을 입력해주세요.', 'error')
            return render_template('edit_project.html', project=project)
        
        # Check if project name already exists (excluding current project)
        existing_project = Project.query.filter(
            Project.name == project_name, 
            Project.id != project_id
        ).first()
        if existing_project:
            flash('이미 존재하는 프로젝트 이름입니다.', 'error')
            return render_template('edit_project.html', project=project)
        
        try:
            project.name = project_name
            project.address = address if address else None
            project.manager_name = manager_name if manager_name else None
            project.manager_phone = manager_phone if manager_phone else None
            project.manager_email = manager_email if manager_email else None
            
            db.session.commit()
            flash('프로젝트 정보가 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('manage_addresses'))
        
        except Exception as e:
            db.session.rollback()
            flash('프로젝트 정보 수정 중 오류가 발생했습니다.', 'error')
            app.logger.error(f"Error updating project: {e}")
    
    return render_template('edit_project.html', project=project)

@app.route('/quick_update_description/<int:photo_id>', methods=['POST'])
def quick_update_description(photo_id):
    """빠른 설명 변경 API"""
    photo = Photo.query.get_or_404(photo_id)
    
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        
        photo.description = description
        db.session.commit()
        
        return jsonify({'success': True, 'message': '설명이 업데이트되었습니다.'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating photo description {photo_id}: {e}")
        return jsonify({'success': False, 'message': '설명 업데이트에 실패했습니다.'})
