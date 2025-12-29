# CSV 파일을 벡터DB로 옮기기 가이드

이 문서는 CSV 파일의 음식점 메뉴 데이터를 벡터DB(ChromaDB)로 옮기는 전체 과정을 단계별로 설명합니다.

## 📋 목차

1. [필수 조건](#필수-조건)
2. [1단계: Python 버전 확인](#1단계-python-버전-확인)
3. [2단계: 가상환경 생성](#2단계-가상환경-생성)
4. [3단계: 필요한 패키지 설치](#3단계-필요한-패키지-설치)
5. [4단계: CSV를 벡터DB로 옮기기](#4단계-csv를-벡터db로-옮기기)
6. [문제 해결](#문제-해결)

---

## 필수 조건

### Python 버전
- **Python 3.11.x** (권장) 또는 **Python 3.12.x**
- ⚠️ **Python 3.14.x는 사용 불가** (ChromaDB 호환성 문제)

### 필요한 파일
- `data/restaurant_menu_data.csv` - 음식점 메뉴 데이터 파일

---

## 1단계: Python 버전 확인

### 명령어
```powershell
python --version
```

### 역할
- 현재 설치된 Python 버전을 확인합니다
- 3.11.x 또는 3.12.x가 나와야 합니다

### 예상 출력
```
Python 3.11.0rc1
```

### Python 3.11이 없다면?
1. https://www.python.org/downloads/ 접속
2. Python 3.11.9 다운로드 및 설치
3. 설치 시 "Add Python to PATH" 체크

---

## 2단계: 가상환경 생성

### 명령어
```powershell
# backend 디렉토리로 이동
cd C:\Users\user\Desktop\testChatBot\backend

# Python 3.11로 가상환경 생성
py -3.11 -m venv venv

# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# Python 버전 확인 (가상환경 내)
python --version
```

### 각 명령어의 역할

#### `cd C:\Users\user\Desktop\testChatBot\backend`
- **역할**: 프로젝트의 backend 디렉토리로 이동
- **이유**: 가상환경과 스크립트가 있는 위치로 이동하기 위해

#### `py -3.11 -m venv venv`
- **역할**: Python 3.11을 사용하여 `venv`라는 이름의 가상환경 생성
- **이유**: 
  - 프로젝트별로 독립적인 Python 환경을 만들기 위해
  - 패키지 버전 충돌을 방지하기 위해
- **결과**: `backend/venv/` 디렉토리가 생성됨

#### `.\venv\Scripts\Activate.ps1`
- **역할**: 생성한 가상환경을 활성화
- **이유**: 이 가상환경에 패키지를 설치하고 사용하기 위해
- **확인**: 명령 프롬프트 앞에 `(venv)`가 표시되면 성공

#### `python --version`
- **역할**: 가상환경 내 Python 버전 확인
- **이유**: 올바른 버전의 Python이 활성화되었는지 확인하기 위해

---

## 3단계: 필요한 패키지 설치

### 방법 1: 전체 패키지 한 번에 설치 (권장)

#### 명령어
```powershell
# pip 업그레이드
python -m pip install --upgrade pip

# requirements.txt의 모든 패키지 설치
pip install -r requirements.txt
```

#### 각 명령어의 역할

##### `python -m pip install --upgrade pip`
- **역할**: pip 패키지 관리자를 최신 버전으로 업그레이드
- **이유**: 최신 pip가 패키지 설치 시 더 나은 의존성 해결을 제공

##### `pip install -r requirements.txt`
- **역할**: `requirements.txt` 파일에 나열된 모든 패키지를 설치
- **설치되는 패키지들**:
  - `chromadb` - 벡터 데이터베이스 (벡터 저장 및 검색)
  - `langchain` - LLM 통합 프레임워크
  - `langchain-community` - LangChain 확장 기능
  - `sentence-transformers` - 한국어 임베딩 모델
  - `fastapi`, `uvicorn` - 웹 서버 (선택사항)
  - 기타 의존성 패키지들

### 방법 2: 필수 패키지만 설치

#### 명령어
```powershell
pip install chromadb langchain langchain-community sentence-transformers
```

#### 각 패키지의 역할

##### `chromadb`
- **역할**: 벡터 데이터베이스
- **용도**: 
  - 문서를 벡터로 변환하여 저장
  - 유사도 검색 수행
  - 메타데이터와 함께 저장

##### `langchain`
- **역할**: LLM 애플리케이션 개발 프레임워크
- **용도**: 
  - 벡터 검색과 LLM을 연결
  - RAG(Retrieval-Augmented Generation) 시스템 구축

##### `langchain-community`
- **역할**: LangChain의 커뮤니티 확장
- **용도**: 
  - 다양한 임베딩 모델 지원
  - 추가 기능 제공

##### `sentence-transformers`
- **역할**: 문장을 벡터로 변환하는 라이브러리
- **용도**: 
  - 한국어 텍스트를 벡터로 변환
  - `jhgan/ko-sroberta-multitask` 모델 사용

### 설치 확인

#### 명령어
```powershell
# ChromaDB 확인
python -c "import chromadb; print('ChromaDB 설치 성공!')"

# LangChain 확인
python -c "import langchain; print('LangChain 설치 성공!')"

# Sentence Transformers 확인
python -c "import sentence_transformers; print('Sentence Transformers 설치 성공!')"
```

#### 역할
- 각 패키지가 제대로 설치되었는지 확인
- 오류가 없으면 다음 단계로 진행 가능

---

## 4단계: CSV를 벡터DB로 옮기기

### 명령어
```powershell
# 가상환경이 활성화되어 있는지 확인 (프롬프트에 (venv) 표시)
# backend 디렉토리에 있는지 확인

# 스크립트 실행
python scripts\init_vectorstore.py
```

### 명령어의 역할

#### `python scripts\init_vectorstore.py`
- **역할**: CSV 파일의 데이터를 읽어서 벡터DB로 변환 및 저장
- **작업 과정**:
  1. CSV 파일 읽기 (`data/restaurant_menu_data.csv`)
  2. 각 메뉴를 문서 형식으로 변환
  3. 한국어 임베딩 모델로 벡터화
  4. ChromaDB에 저장
  5. 테스트 검색 수행

### 예상 출력

```
벡터 저장소 초기화 시작 (CSV 파일에서)
CSV 파일 로딩: C:\Users\user\Desktop\testChatBot\backend\data\restaurant_menu_data.csv
총 50개 음식점 데이터 로드 완료
기존 컬렉션 삭제 완료
477개 문서를 벡터 저장소에 추가 중...
진행 중: 50/477
진행 중: 100/477
...
벡터 저장소 초기화 완료: 477개 문서 저장
테스트 검색 수행: '전주비빔밥'
테스트 검색 결과: 3개 결과
 1. 비빔밥 (점수: 0.xxxx)
 2. ...
```

### 각 단계 설명

#### 1. CSV 파일 읽기
- **역할**: `restaurant_menu_data.csv` 파일에서 데이터를 읽어옵니다
- **데이터 구조**: 음식점 ID, 음식점명, 주소, 카테고리, 메뉴 ID, 메뉴명, 가격, 칼로리, 재료 원산지

#### 2. 문서 형식 변환
- **역할**: CSV 데이터를 검색 가능한 텍스트 문서로 변환
- **형식 예시**:
  ```
  음식점명: 전주한정식
  주소: 전주시 덕진구 금암동 569-466
  카테고리: 한식
  
  메뉴: 닭볶음탕
  가격: 13086원
  칼로리: 609kcal
  재료 원산지: 닭고기(국내산), 감자(국내산), 당근(국내산), 양파(국내산)
  ```

#### 3. 벡터화
- **역할**: 텍스트 문서를 숫자 벡터로 변환
- **모델**: `jhgan/ko-sroberta-multitask` (한국어 전용)
- **차원**: 768차원 벡터
- **시간**: 477개 문서 변환에 약 1-2분 소요 (첫 실행 시 모델 다운로드 포함)

#### 4. ChromaDB 저장
- **역할**: 벡터, 문서, 메타데이터를 ChromaDB에 저장
- **저장 위치**: `backend/chroma_db/`
- **컬렉션명**: `restaurant_menu`
- **저장 내용**:
  - 문서 텍스트
  - 벡터 (768차원)
  - 메타데이터 (음식점명, 주소, 메뉴명, 가격 등)
  - 고유 ID

#### 5. 테스트 검색
- **역할**: 저장이 제대로 되었는지 검색으로 확인
- **검색어**: "전주비빔밥"
- **결과**: 유사한 메뉴들을 찾아서 표시

### 저장 결과 확인

#### 저장 위치
```
backend/chroma_db/
├── chroma.sqlite3          # 메인 데이터베이스 파일
└── [UUID]/                 # 벡터 인덱스 파일들
    ├── data_level0.bin
    ├── header.bin
    ├── length.bin
    └── link_lists.bin
```

#### 저장된 데이터
- **문서 수**: 477개 (각 메뉴별로 1개 문서)
- **벡터 차원**: 768차원
- **컬렉션명**: `restaurant_menu`

---

## 문제 해결

### 오류 1: Python 버전이 3.14인 경우

**증상**:
```
pydantic.v1.errors.ConfigError: unable to infer type
```

**원인**: Python 3.14는 ChromaDB와 호환되지 않음

**해결**:
```powershell
# Python 3.11로 가상환경 재생성
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### 오류 2: chromadb를 찾을 수 없음

**증상**:
```
ModuleNotFoundError: No module named 'chromadb'
```

**원인**: chromadb 패키지가 설치되지 않음

**해결**:
```powershell
pip install chromadb
```

---

### 오류 3: 가상환경 활성화 실패

**증상**:
```
cannot be loaded because running scripts is disabled
```

**원인**: PowerShell 실행 정책 제한

**해결**:
```powershell
# 실행 정책 변경 (관리자 권한 필요)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 다시 활성화 시도
.\venv\Scripts\Activate.ps1
```

---

### 오류 4: CSV 파일을 찾을 수 없음

**증상**:
```
CSV 파일을 찾을 수 없습니다: ...
```

**원인**: CSV 파일 경로가 잘못되었거나 파일이 없음

**해결**:
1. `backend/data/restaurant_menu_data.csv` 파일이 있는지 확인
2. 파일 이름과 경로가 정확한지 확인

---

### 오류 5: 임베딩 모델 다운로드 실패

**증상**: 모델 다운로드 중 오류 발생

**원인**: 인터넷 연결 문제 또는 Hugging Face 접근 제한

**해결**:
1. 인터넷 연결 확인
2. 방화벽 설정 확인
3. Hugging Face 계정 로그인 (선택사항)

---

## 전체 작업 순서 요약

```powershell
# 1. 디렉토리 이동
cd C:\Users\user\Desktop\testChatBot\backend

# 2. Python 버전 확인
python --version  # 3.11.x 또는 3.12.x여야 함

# 3. 가상환경 생성
py -3.11 -m venv venv

# 4. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 5. pip 업그레이드
python -m pip install --upgrade pip

# 6. 패키지 설치
pip install -r requirements.txt

# 7. 설치 확인
python -c "import chromadb; print('OK')"

# 8. CSV를 벡터DB로 옮기기
python scripts\init_vectorstore.py
```

---

## 다음 단계

벡터DB에 데이터가 저장되면:
- 챗봇에서 음식점 메뉴 검색 기능 사용 가능
- RAG(Retrieval-Augmented Generation) 시스템 구축 가능
- 유사도 기반 메뉴 추천 기능 구현 가능

---

**마지막 업데이트**: 2025-12-24

