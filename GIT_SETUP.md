# GitHub 업로드 가이드

## 1. Git 설치 확인 및 설치

### Git이 설치되어 있지 않은 경우

1. Git 공식 웹사이트에서 다운로드: https://git-scm.com/download/win
2. 설치 후 PowerShell을 재시작
3. 설치 확인:
   ```powershell
   git --version
   ```

## 2. GitHub 저장소 생성

1. GitHub.com에 로그인
2. 새 저장소 생성 (New Repository)
3. 저장소 이름 입력 (예: testChatBot)
4. Public 또는 Private 선택
5. "Create repository" 클릭
6. 저장소 URL 복사 (예: https://github.com/username/testChatBot.git)

## 3. 로컬 Git 저장소 초기화 및 업로드

PowerShell에서 프로젝트 폴더로 이동한 후 다음 명령어 실행:

```powershell
# 1. Git 저장소 초기화
git init

# 2. 모든 파일 추가
git add .

# 3. 첫 번째 커밋
git commit -m "Initial commit: 챗봇 프로젝트 초기 설정"

# 4. GitHub 저장소 연결 (YOUR_GITHUB_REPO_URL을 실제 URL로 변경)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 5. 브랜치 이름을 main으로 설정
git branch -M main

# 6. GitHub에 업로드
git push -u origin main
```

## 4. 인증 문제 해결

### Personal Access Token 사용 (GitHub에서 패스워드 인증이 비활성화됨)

1. GitHub.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 권한 선택 (repo 권한 필수)
4. 토큰 생성 후 복사
5. push 시 패스워드 대신 토큰 사용

또는 GitHub Desktop 사용 (GUI 도구):
- https://desktop.github.com/ 다운로드 및 설치

## 5. 이후 업데이트 방법

파일 변경 후:

```powershell
# 변경사항 확인
git status

# 변경사항 추가
git add .

# 커밋
git commit -m "변경 사항 설명"

# GitHub에 업로드
git push
```

## 문제 해결

### Git이 인식되지 않는 경우
- PowerShell 재시작
- Git이 설치되었는지 확인: `where.exe git`
- 환경 변수 PATH에 Git 경로가 포함되어 있는지 확인

### 인증 오류
- Personal Access Token 사용
- GitHub Desktop 사용
- SSH 키 설정 (고급)

### 큰 파일 업로드 오류
- .gitignore 파일 확인
- Git LFS 사용 (큰 파일용)


