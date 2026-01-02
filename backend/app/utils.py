"""
유틸리티 함수: 로깅, 환경변수, 헬퍼 함수

이 파일의 역할:
- 애플리케이션 전반에서 사용되는 공통 유틸리티 함수들을 제공
- 환경변수 관리 (.env 파일 로드 및 읽기)
- 로깅 설정 및 로거 인스턴스 제공
- 프로젝트 경로 설정 (BASE_DIR, CHROMA_DB_PATH, DATA_DIR)
- 환경변수 기반 설정값 관리 (DB 연결 정보, API 키 등)

왜 필요한가:
- 코드 중복을 방지하고 재사용 가능한 기능을 중앙화
- 환경변수를 한 곳에서 관리하여 유지보수성 향상
- 로깅을 표준화하여 디버깅과 모니터링 용이
- 다른 모듈들이 환경 설정값에 쉽게 접근할 수 있도록 함

주요 기능:
- get_env(): 필수 환경변수 가져오기 (없으면 에러 발생)
- get_env_optional(): 선택적 환경변수 가져오기 (기본값 제공)
- logger: 전역 로거 인스턴스 (로깅 설정 포함)
- 데이터베이스, API 키, 경로 등의 환경 설정값들
"""

import logging
from pathlib import Path

# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).parent.parent

# ChromaDB 경로
CHROMA_DB_PATH = BASE_DIR / "chroma_db"
CHROMA_DB_PATH.mkdir(exist_ok=True)

# 데이터 디렉토리 경로
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


def validate_question(question: str) -> tuple[bool, str]:
    """
    질문이 전주 음식점/음식 관련인지 검증
    
    Args:
        question: 사용자 질문
        
    Returns:
        (is_valid, rejection_message): 
        - is_valid: True면 허용, False면 거절
        - rejection_message: 거절 시 출력할 메시지
    """
    # 거절 메시지 (고정)
    REJECTION_MESSAGE = "이 서비스는 전주 지역 음식점 추천만 제공하고 있어요.\n전주 맛집이나 음식 관련 질문을 해 주세요 🙂"
    
    question_lower = question.lower()
    
    # 1. 금지 키워드 체크 (무조건 거절)
    forbidden_keywords = [
        "노래", "음악", "가수", "앨범", "곡", "뮤직",
        "영화", "드라마", "배우", "감독", "영화관", "극장",
        "번역", "translate", "translation",
        "코딩", "프로그래밍", "코드", "개발", "프로그래머",
        "수학", "수식", "계산", "방정식",
        "날씨", "기상", "온도", "비", "눈",
        "뉴스", "시사", "정치", "경제"
    ]
    
    for keyword in forbidden_keywords:
        if keyword in question_lower:
            return (False, REJECTION_MESSAGE)
    
    # 2. 허용 키워드 체크 (하나라도 있으면 허용)
    allowed_keywords = [
        "음식", "식당", "맛집", "음식점", "레스토랑",
        "메뉴", "음식 메뉴", "요리",
        "가격", "비용", "돈", "원",
        "칼로리", "열량", "다이어트",
        "전주", "전주시",
        "배달", "포장", "테이크아웃",
        "추천", "어디", "어떤", "맛있는", "좋은"
    ]
    
    for keyword in allowed_keywords:
        if keyword in question_lower:
            return (True, "")
    
    # 3. 허용 키워드가 없으면 거절
    return (False, REJECTION_MESSAGE)