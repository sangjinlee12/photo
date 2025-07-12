# 에스에스전력 사진 관리시스템

건설 현장 사진 및 프로젝트 관리 웹 플랫폼으로, 공사 프로젝트의 효율적인 문서화와 추적을 지원합니다.

## 주요 기능

- **프로젝트 관리**: 건설 프로젝트 생성 및 관리
- **사진 업로드**: 프로젝트별 다중 사진 업로드 (최대 50MB/파일)
- **사진 관리**: 조회, 다운로드, 일괄 편집, 개별 편집
- **메타데이터 추출**: 파일명에서 자동으로 날짜와 정보 추출
- **준공사진첩**: 전문적인 A4 사이즈 준공사진첩 자동 생성
- **현장주소 관리**: 주소와 담당자 정보 저장, 카카오맵 연동 길찾기
- **일괄 처리**: 체크박스 기반 다중 선택 및 일괄 수정

## 기술 스택

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Image Processing**: Pillow (PIL)
- **Deployment**: Gunicorn

## 배포 방법

### 1. Heroku 배포

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### 2. 수동 배포

#### 환경 설정
```bash
# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값으로 설정
```

#### 로컬 실행
```bash
# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 애플리케이션 실행
gunicorn main:app
```

### 3. GitHub에서 Heroku 연동

1. **GitHub 저장소 생성**
   - GitHub에서 새 저장소 생성
   - 코드를 해당 저장소에 푸시

2. **Heroku 앱 생성**
   - Heroku 계정 생성/로그인
   - "Create new app" 클릭
   - 앱 이름 설정 (예: ss-electric-photo-manager)

3. **GitHub 연동**
   - Heroku 대시보드에서 Deploy 탭 선택
   - Deployment method에서 "GitHub" 선택
   - 저장소 검색 후 연결

4. **환경 변수 설정**
   - Settings 탭에서 "Config Vars" 클릭
   - 다음 변수들 추가:
     - `SESSION_SECRET`: 랜덤한 비밀 키
     - `FLASK_ENV`: production

5. **PostgreSQL 애드온 추가**
   - Resources 탭에서 "Add-ons" 검색
   - "Heroku Postgres" 선택하여 추가

6. **수동 배포**
   - Deploy 탭에서 "Manual deploy" 섹션
   - 브랜치 선택 후 "Deploy Branch" 클릭

7. **자동 배포 설정 (선택사항)**
   - "Automatic deploys" 섹션에서 브랜치 선택
   - "Enable Automatic Deploys" 클릭

## 환경 변수

| 변수명 | 설명 | 필수 여부 |
|--------|------|-----------|
| `DATABASE_URL` | PostgreSQL 데이터베이스 URL | 필수 |
| `SESSION_SECRET` | Flask 세션 암호화 키 | 필수 |
| `FLASK_ENV` | Flask 환경 (production/development) | 선택 |

## 파일 구조

```
├── app.py              # Flask 애플리케이션 설정
├── main.py             # 애플리케이션 엔트리포인트
├── models.py           # 데이터베이스 모델
├── routes.py           # 라우트 핸들러
├── templates/          # HTML 템플릿
├── static/             # CSS, JS, 이미지 파일
├── uploads/            # 업로드된 사진 저장소
├── Procfile            # Heroku 배포 설정
├── runtime.txt         # Python 버전 명시
├── app.json            # Heroku 앱 메타데이터
└── requirements.txt    # Python 의존성
```

## 사용법

1. **프로젝트 생성**: 새 건설 프로젝트 생성
2. **사진 업로드**: 프로젝트별 현장 사진 업로드
3. **정보 관리**: 사진별 위치, 날짜, 설명 정보 입력/수정
4. **준공사진첩**: 완성된 프로젝트의 준공사진첩 생성 및 다운로드

## 라이센스

© 2025 주식회사 에스에스전력. All rights reserved.