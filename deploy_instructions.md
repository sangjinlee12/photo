# GitHub에서 Heroku로 배포하기

## 1단계: GitHub 저장소 준비

### GitHub 저장소 생성 및 코드 업로드
```bash
# 로컬에서 Git 초기화 (아직 안했다면)
git init

# 모든 파일 추가
git add .

# 첫 번째 커밋
git commit -m "초기 커밋: 에스에스전력 사진 관리시스템"

# GitHub 저장소 추가 (YOUR_USERNAME을 실제 GitHub 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/ss-electric-photo-manager.git

# GitHub에 푸시
git push -u origin main
```

## 2단계: Heroku 계정 및 앱 생성

1. **Heroku 계정 생성**
   - https://heroku.com 에서 무료 계정 생성

2. **새 앱 생성**
   - Heroku 대시보드에서 "Create new app" 클릭
   - 앱 이름: `ss-electric-photo-manager` (또는 원하는 이름)
   - 지역: United States 선택

## 3단계: GitHub 연동

1. **Deploy 탭 선택**
   - 생성된 앱의 대시보드에서 "Deploy" 탭 클릭

2. **GitHub 연결**
   - "Deployment method" 섹션에서 "GitHub" 선택
   - "Connect to GitHub" 버튼 클릭하여 GitHub 계정 연결

3. **저장소 연결**
   - "Connect to GitHub" 섹션에서 저장소명 검색
   - `ss-electric-photo-manager` 검색 후 "Connect" 클릭

## 4단계: 데이터베이스 추가

1. **Resources 탭 선택**
   - 앱 대시보드에서 "Resources" 탭 클릭

2. **PostgreSQL 애드온 추가**
   - "Add-ons" 검색창에 "postgres" 입력
   - "Heroku Postgres" 선택
   - Plan은 "Hobby Dev - Free" 선택
   - "Submit Order Form" 클릭

## 5단계: 환경 변수 설정

1. **Settings 탭 선택**
   - 앱 대시보드에서 "Settings" 탭 클릭

2. **Config Vars 설정**
   - "Config Vars" 섹션에서 "Reveal Config Vars" 클릭
   - 다음 변수들 추가:

| Key | Value |
|-----|-------|
| `SESSION_SECRET` | `your-random-secret-key-here-make-it-long-and-random` |
| `FLASK_ENV` | `production` |

   > 참고: DATABASE_URL은 PostgreSQL 애드온 추가시 자동으로 설정됩니다.

## 6단계: 배포 실행

1. **수동 배포**
   - "Deploy" 탭으로 돌아가기
   - "Manual deploy" 섹션에서 `main` 브랜치 선택
   - "Deploy Branch" 버튼 클릭

2. **배포 진행 상황 확인**
   - 배포 로그를 확인하여 성공적으로 완료되는지 모니터링
   - "Your app was successfully deployed" 메시지 확인

3. **앱 실행 확인**
   - "View" 버튼 클릭하여 배포된 앱 확인
   - 또는 `https://your-app-name.herokuapp.com` 직접 접속

## 7단계: 자동 배포 설정 (선택사항)

1. **자동 배포 활성화**
   - "Deploy" 탭의 "Automatic deploys" 섹션
   - "Enable Automatic Deploys" 클릭
   - 이제 main 브랜치에 푸시할 때마다 자동으로 배포됩니다

## 8단계: 도메인 설정 (선택사항)

1. **커스텀 도메인 추가**
   - "Settings" 탭의 "Domains" 섹션
   - "Add domain" 클릭하여 원하는 도메인 추가

## 배포 후 확인사항

✅ **기능 테스트**
- 프로젝트 생성
- 사진 업로드 (작은 파일로 테스트)
- 사진 조회 및 다운로드
- 준공사진첩 생성

✅ **성능 확인**
- 페이지 로딩 속도
- 이미지 표시 속도

## 문제 해결

### 일반적인 문제들

1. **앱이 시작되지 않는 경우**
   ```bash
   # Heroku CLI로 로그 확인
   heroku logs --tail -a your-app-name
   ```

2. **데이터베이스 연결 문제**
   - Config Vars에서 DATABASE_URL 확인
   - PostgreSQL 애드온이 제대로 추가되었는지 확인

3. **파일 업로드 문제**
   - Heroku의 임시 파일 시스템 제한사항 확인
   - 대용량 파일의 경우 클라우드 스토리지 고려

### 지원 및 문의

- GitHub Issues: 프로젝트 저장소의 Issues 탭
- 이메일: info@sselectric.co.kr

## 업데이트 방법

```bash
# 코드 수정 후
git add .
git commit -m "업데이트 설명"
git push origin main

# 자동 배포가 설정되어 있다면 자동으로 배포됩니다
# 수동 배포의 경우 Heroku 대시보드에서 다시 배포 실행
```