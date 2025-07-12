# 에스에스전력 사진 관리시스템 (SS Electric Photo Management System)

## Overview

This is a Flask-based photo management web application designed for SS Electric (주식회사 에스에스전력). The system allows users to create construction projects, upload photos to specific projects, view photos in a gallery format, and download photos individually or in bulk. The application is built with a simple, intuitive interface using Bootstrap and supports multiple image formats.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite as default (configurable via environment variables)
- **File Storage**: Local filesystem storage in an `uploads` directory
- **Image Processing**: PIL (Python Imaging Library) for thumbnail generation and image optimization

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's built-in templating)
- **CSS Framework**: Bootstrap 5 with dark theme
- **JavaScript**: Vanilla JavaScript for interactive features
- **Icons**: Font Awesome for consistent iconography

### Database Schema
The application uses a simple relational model:
- **Project** table: Stores project information (id, name, created_at)
- **Photo** table: Stores photo metadata (id, project_id, filename, filepath, uploaded_at)
- One-to-many relationship between Project and Photo with cascade delete

## Key Components

### Core Models (`models.py`)
- **Project Model**: Represents construction projects with basic metadata
- **Photo Model**: Represents uploaded photos linked to projects via foreign key

### Route Handlers (`routes.py`)
- Project management (create, view, delete)
- Photo upload with multiple file support
- Photo viewing with thumbnail and full-size display
- Bulk download functionality (ZIP archives)
- Individual photo download and deletion

### Frontend Templates
- **Base Template**: Provides consistent navigation and layout
- **Index**: Project listing dashboard
- **Create Project**: Simple form for project creation
- **Upload Photos**: Multi-file upload interface with preview
- **View Photos**: Gallery view with thumbnail grid

### Static Assets
- **CSS**: Custom styling for photo galleries and responsive design
- **JavaScript**: File preview, modal functionality, and upload progress

## Data Flow

1. **Project Creation**: User creates a project → Database entry created → Project directory created in filesystem
2. **Photo Upload**: User selects photos → Files validated and processed → Stored in project-specific directory → Database metadata recorded
3. **Photo Viewing**: User requests gallery → Database queried for project photos → Thumbnails generated on-demand → Gallery rendered
4. **Download**: User requests download → Files retrieved from filesystem → ZIP archive created (for bulk) or direct file served

## External Dependencies

### Python Packages
- **Flask**: Web framework and routing
- **Flask-SQLAlchemy**: Database ORM integration
- **Werkzeug**: WSGI utilities and file handling
- **Pillow (PIL)**: Image processing and thumbnail generation

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Font Awesome**: Icon library
- **Vanilla JavaScript**: No heavy frontend frameworks

### Infrastructure
- **ProxyFix**: For handling reverse proxy headers
- **SQLite**: Default database (production can use PostgreSQL via DATABASE_URL)

## Deployment Strategy

### Configuration
- **Environment Variables**: 
  - `DATABASE_URL`: Database connection string
  - `SESSION_SECRET`: Flask session encryption key
- **File Storage**: Local uploads directory (50MB max file size)
- **Database**: Automatic table creation on startup

### Production Considerations
- Database can be switched to PostgreSQL by changing DATABASE_URL
- File uploads stored locally (consider cloud storage for scaling)
- Session management uses secure cookies
- Debug mode configurable via environment

### Development Setup
- Debug mode enabled by default
- SQLite database for easy local development
- Hot reloading supported
- Comprehensive logging configured

## Changelog
- July 08, 2025. Initial setup
- July 08, 2025. PostgreSQL 데이터베이스 연결로 데이터 영구 보존 구현
- July 09, 2025. 현장주소 관리 기능 추가 (주소, 담당자 정보, 카카오맵 연동)
- July 10, 2025. 체크박스 기반 일괄 수정 기능 구현 (선택모드, 촬영위치/날짜/설명 일괄변경)
- July 10, 2025. 자동 이미지 압축 및 파일명 기반 정보 추출 기능 추가 (YYYY-MM-DD_NN 패턴)
- July 10, 2025. 일괄수정 및 개별수정 모달에 공사 작업 종류 드롭다운 리스트 추가
- July 11, 2025. 시스템 명칭을 "에스에스전력 사진 관리시스템"으로 변경
- July 12, 2025. 파일 업로드 크기 제한 최적화 (개별 파일 50MB, 총 500MB)
- July 12, 2025. GitHub/Heroku 배포를 위한 설정 파일 생성 (Procfile, app.json, requirements.txt, .gitignore, README.md)

## User Preferences

Preferred communication style: Simple, everyday language in Korean.
Company branding: 주식회사 에스에스전력 (SS Electric Co., Ltd.)