from app import db
from datetime import datetime

class Project(db.Model):
    """Model for construction projects"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500), nullable=True)
    manager_name = db.Column(db.String(100), nullable=True)
    manager_phone = db.Column(db.String(20), nullable=True)
    manager_email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to photos
    photos = db.relationship('Photo', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Project {self.name}>'

class Photo(db.Model):
    """Model for uploaded photos"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    photo_location = db.Column(db.String(200), nullable=True)  # 사진 촬영 위치
    photo_date = db.Column(db.Date, nullable=True)  # 사진 촬영 날짜
    description = db.Column(db.String(500), nullable=True)  # 사진 설명
    
    def __repr__(self):
        return f'<Photo {self.filename}>'
