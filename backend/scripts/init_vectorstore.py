"""
벡터 DB 초기화 스크립트
음식점 메뉴 데이터를 벡터 DB에 저장

이 파일의 역할:
- CSV 파일에서 음식점 메뉴 데이터를 읽어옴
- 각 메뉴 정보를 검색 가능한 텍스트 문서로 변환
- 텍스트를 벡터(숫자 배열)로 변환하여 ChromaDB에 저장
- RAG 시스템이 사용할 검색 가능한 데이터를 준비

왜 필요한가:
- 애플리케이션 시작 전에 벡터 DB를 준비해야 함
- 음식점 메뉴 정보가 변경되면 벡터 DB도 업데이트 필요
- 배치 작업으로 대량의 데이터를 한 번에 처리
- 초기 설정 및 데이터 마이그레이션 시 사용

실행 흐름:
1. CSV 파일에서 데이터 읽기
2. 각 메뉴를 검색 가능한 텍스트 문서로 변환
3. 문서를 벡터(숫자 배열)로 변환
4. 벡터와 메타데이터를 ChromaDB에 저장
5. 테스트 검색 수행하여 정상 작동 확인

사용 방법:
- python scripts/init_vectorstore.py
"""

# 표준 라이브러리 import: Python 기본 기능들을 사용하기 위함
import sys  # 시스템 관련 기능 (경로 설정 등)
import csv  # CSV 파일 읽기/쓰기 기능
from pathlib import Path  # 파일 경로를 다루는 모듈 (Windows/Mac/Linux 호환)
from collections import defaultdict  # 기본값이 있는 딕셔너리 생성 (음식점별로 메뉴 그룹화에 사용)

# 프로젝트 루트 경로 설정
# __file__은 현재 파일의 경로를 의미함 (예: backend/scripts/init_vectorstore.py)
# .parent는 부모 디렉토리 (backend/scripts)
# .parent.parent는 그 부모 디렉토리 (backend)
project_root = Path(__file__).parent.parent

# Python이 모듈을 찾을 수 있도록 프로젝트 루트를 경로에 추가
# 이렇게 하면 'from app.vectorstore import VectorStore' 같은 import가 작동함
sys.path.insert(0, str(project_root))

# 프로젝트 내부 모듈 import
from app.vectorstore import VectorStore  # 벡터 저장소 클래스 (ChromaDB와 통신)
from app.utils import logger  # 로그를 남기는 기능 (에러 추적, 디버깅용)


def format_restaurant_document(row):
    """
    CSV 한 행의 데이터를 검색 가능한 텍스트 문서로 변환하는 함수
    
    예를 들어 CSV의 한 행:
    - restaurant_name: "전주 비빔밥집"
    - menu_name: "전주 비빔밥"
    - price: "8000"
    
    이 함수를 거치면 다음과 같은 텍스트로 변환됨:
    "음식점명: 전주 비빔밥집
    주소: 전주시...
    카테고리: 한식
    
    메뉴: 전주 비빔밥
    가격: 8000원
    ..."
    
    Args:
        row (dict): CSV 파일의 한 행을 딕셔너리로 변환한 것
                    예: {'restaurant_name': '전주 비빔밥집', 'menu_name': '비빔밥', ...}
    
    Returns:
        str: 검색 가능한 형식의 텍스트 문서
    """
    # 텍스트 문서의 각 부분을 담을 리스트 초기화
    # 예: ["음식점명: 전주 비빔밥집", "주소: 전주시...", ...]
    doc_parts = []
    
    # ===== 음식점 기본 정보를 텍스트로 변환 =====
    # f"..." 는 f-string 문법으로, 변수값을 문자열 안에 삽입함
    # 예: f"음식점명: {row['restaurant_name']}" → "음식점명: 전주 비빔밥집"
    doc_parts.append(f"음식점명: {row['restaurant_name']}")  # 음식점 이름 추가
    doc_parts.append(f"주소: {row['address']}")  # 주소 추가
    doc_parts.append(f"카테고리: {row['category']}")  # 카테고리 추가 (한식, 중식 등)
    
    # ===== 메뉴 정보를 텍스트로 변환 =====
    doc_parts.append(f"\n메뉴: {row['menu_name']}")  # \n은 줄바꿈, 메뉴 이름 추가
    doc_parts.append(f"가격: {row['price']}원")  # 가격 정보 추가
    doc_parts.append(f"칼로리: {row['calories']}kcal")  # 칼로리 정보 추가
    doc_parts.append(f"재료 원산지: {row['ingredients_origin']}")  # 재료 원산지 정보 추가
    
    # 리스트의 각 요소를 줄바꿈(\n)으로 연결하여 하나의 문자열로 만듦
    # 예: ["음식점명: 전주 비빔밥집", "주소: ..."] → "음식점명: 전주 비빔밥집\n주소: ..."
    return "\n".join(doc_parts)


def load_csv_data(csv_path):
    """
    CSV 파일에서 음식점과 메뉴 데이터를 읽어서 구조화하는 함수
    
    CSV 파일 구조 예시:
    restaurant_id, restaurant_name, menu_id, menu_name, price, calories, ...
    1, "전주 비빔밥집", 101, "전주 비빔밥", 8000, 500, ...
    1, "전주 비빔밥집", 102, "불고기 비빔밥", 9000, 600, ...
    2, "맛있는 치킨집", 201, "양념치킨", 15000, 800, ...
    
    이 함수는 이를 다음과 같이 그룹화함:
    {
        "1": {
            "info": {"restaurant_name": "전주 비빔밥집", ...},
            "menus": [
                {"menu_name": "전주 비빔밥", ...},
                {"menu_name": "불고기 비빔밥", ...}
            ]
        },
        "2": {...}
    }
    
    Args:
        csv_path (Path): CSV 파일의 경로 (예: Path("data/restaurant_menu_data.csv"))
    
    Returns:
        dict: 음식점 ID를 키로 하고, 음식점 정보와 메뉴 리스트를 값으로 하는 딕셔너리
    """
    # defaultdict: 존재하지 않는 키로 접근하면 자동으로 기본값을 생성하는 딕셔너리
    # lambda: {"info": None, "menus": []} 형태의 딕셔너리를 기본값으로 생성
    # 예: restaurants["1"]에 처음 접근하면 자동으로 {"info": None, "menus": []} 생성
    restaurants = defaultdict(lambda: {"info": None, "menus": []})
    
    # CSV 파일 열기
    # 'r': 읽기 모드
    # encoding='utf-8-sig': UTF-8 인코딩 사용 (한국어 및 특수문자 처리, -sig는 BOM 제거)
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        # DictReader: CSV의 각 행을 딕셔너리로 읽어줌
        # 첫 번째 행(헤더)를 키로 사용
        # 예: 첫 행이 "restaurant_id,restaurant_name"이면
        #     row = {'restaurant_id': '1', 'restaurant_name': '전주 비빔밥집', ...}
        reader = csv.DictReader(f)
        
        # CSV 파일의 각 행을 하나씩 처리
        for row in reader:
            # 현재 행의 음식점 ID 가져오기
            restaurant_id = row['restaurant_id']
            
            # ===== 음식점 정보 저장 (각 음식점의 첫 번째 메뉴 행에서만) =====
            # info가 None이면 아직 이 음식점 정보를 저장하지 않았다는 의미
            if restaurants[restaurant_id]["info"] is None:
                # 음식점 기본 정보 딕셔너리 생성 및 저장
                restaurants[restaurant_id]["info"] = {
                    "restaurant_id": restaurant_id,  # 음식점 ID
                    "restaurant_name": row['restaurant_name'],  # 음식점 이름
                    "address": row['address'],  # 주소
                    "category": row['category']  # 카테고리 (한식, 중식 등)
                }
            
            # ===== 메뉴 정보 추가 (각 행마다 실행됨) =====
            # 같은 음식점의 메뉴들이 계속 추가됨
            restaurants[restaurant_id]["menus"].append({
                "menu_id": row['menu_id'],  # 메뉴 ID
                "menu_name": row['menu_name'],  # 메뉴 이름
                "price": row['price'],  # 가격
                "calories": row['calories'],  # 칼로리
                "ingredients_origin": row['ingredients_origin']  # 재료 원산지
            })
    
    # 구조화된 데이터 반환
    return restaurants


def init_vectorstore_from_csv():
    """
    CSV 파일에서 데이터를 읽어서 벡터 데이터베이스에 저장하는 메인 함수
    
    전체 프로세스:
    1. CSV 파일에서 데이터 읽기
    2. 각 메뉴를 텍스트 문서로 변환
    3. 텍스트를 벡터(숫자 배열)로 변환
    4. 벡터와 메타데이터를 ChromaDB에 저장
    5. 테스트 검색으로 정상 작동 확인
    """
    try:
        # ===== 1단계: 초기화 시작 메시지 =====
        print("벡터 저장소 초기화 시작 (CSV 파일에서)")  # 사용자에게 화면에 출력
        logger.info("벡터 저장소 초기화 시작 (CSV 파일에서)")  # 로그 파일에도 기록
        
        # ===== 2단계: CSV 파일 경로 설정 =====
        # Path 객체를 / 연산자로 연결하여 경로 생성 (Windows/Mac/Linux 모두 호환)
        # 예: backend/data/restaurant_menu_data.csv
        csv_path = project_root / "data" / "restaurant_menu_data.csv"
        
        # 파일이 실제로 존재하는지 확인
        if not csv_path.exists():
            logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
            return  # 파일이 없으면 함수 종료
        
        # ===== 3단계: CSV 파일에서 데이터 로드 =====
        print(f"CSV 파일 로딩: {csv_path}")  # 사용자에게 진행 상황 알림
        logger.info(f"CSV 파일 로딩: {csv_path}")  # 로그 기록
        
        # load_csv_data 함수 호출: CSV 파일을 읽어서 구조화된 딕셔너리로 변환
        restaurants = load_csv_data(csv_path)
        
        # 로드된 음식점 개수 출력
        print(f"총 {len(restaurants)}개 음식점 데이터 로드 완료")
        logger.info(f"총 {len(restaurants)}개 음식점 데이터 로드 완료")
        
        # ===== 4단계: 기존 벡터 저장소 초기화 (선택적) =====
        # VectorStore 객체 생성 (이때 ChromaDB와 연결됨)
        vectorstore = VectorStore()
        
        try:
            # 기존 컬렉션(데이터 그룹) 삭제
            # 이전에 저장된 데이터를 지우고 새로 시작하려면 이렇게 함
            vectorstore.delete_collection()
            logger.info("기존 컬렉션 삭제 완료")
        except:
            # 컬렉션이 없거나 삭제할 수 없으면 에러 무시하고 계속 진행
            logger.info("기존 컬렉션이 없거나 삭제 불가")
        
        # ===== 5단계: 새 벡터 저장소 생성 =====
        # 새로운 VectorStore 객체 생성 (새 컬렉션을 만들거나 기존 컬렉션에 접근)
        vectorstore = VectorStore()
        
        # ===== 6단계: 문서 및 메타데이터 준비 =====
        # 벡터 DB에 저장할 데이터를 담을 리스트들 초기화
        texts = []  # 텍스트 문서 리스트 (예: "음식점명: 전주 비빔밥집\n...")
        metadatas = []  # 메타데이터 리스트 (예: {"restaurant_name": "전주 비빔밥집", "price": "8000"})
        ids = []  # 고유 ID 리스트 (예: "restaurant_1_menu_101")
        
        # 각 음식점에 대해 반복 처리
        # .items()는 딕셔너리의 키와 값을 함께 가져옴
        # 예: restaurant_id="1", data={"info": {...}, "menus": [...]}
        for restaurant_id, data in restaurants.items():
            # 음식점 기본 정보 추출
            restaurant_info = data["info"]
            # 해당 음식점의 메뉴 리스트 추출
            menus = data["menus"]
            
            # ===== 각 메뉴마다 별도의 문서로 생성 =====
            # 한 음식점에 여러 메뉴가 있으면 각각을 독립적인 문서로 만듦
            # 이렇게 하면 "비빔밥"으로 검색했을 때 정확한 메뉴를 찾을 수 있음
            for menu in menus:
                # 음식점 정보와 메뉴 정보를 하나의 딕셔너리로 합치기
                # ** 연산자는 딕셔너리를 펼쳐서 내용을 복사함
                # 예: {"restaurant_name": "전주 비빔밥집", "menu_name": "비빔밥", ...}
                row = {
                    **restaurant_info,  # 음식점 정보 복사
                    **menu  # 메뉴 정보 복사 (같은 키가 있으면 menu가 우선)
                }
                
                # ===== 문서 텍스트 생성 =====
                # format_restaurant_document 함수 호출
                # CSV 행 데이터를 검색 가능한 텍스트 문서로 변환
                doc_text = format_restaurant_document(row)
                texts.append(doc_text)  # 텍스트 문서 리스트에 추가
                
                # ===== 메타데이터 생성 =====
                # 검색 결과에서 필터링하거나 표시할 때 사용할 정보
                # 예: "가격이 10000원 이하인 메뉴만" 같은 필터링에 사용
                metadata = {
                    "restaurant_id": restaurant_info["restaurant_id"],  # 음식점 ID
                    "restaurant_name": restaurant_info["restaurant_name"],  # 음식점 이름
                    "address": restaurant_info["address"],  # 주소
                    "category": restaurant_info["category"],  # 카테고리
                    "menu_id": menu["menu_id"],  # 메뉴 ID
                    "menu_name": menu["menu_name"],  # 메뉴 이름
                    "price": menu["price"],  # 가격 (필터링에 사용 가능)
                    "calories": menu["calories"]  # 칼로리 (필터링에 사용 가능)
                }
                metadatas.append(metadata)  # 메타데이터 리스트에 추가
                
                # ===== 고유 ID 생성 =====
                # 벡터 DB에서 각 문서를 식별하기 위한 고유한 ID
                # 예: "restaurant_1_menu_101" (음식점 1번의 메뉴 101번)
                ids.append(f"restaurant_{restaurant_id}_menu_{menu['menu_id']}")
        
        # ===== 7단계: 벡터 저장소에 추가 =====
        # 벡터 DB에 실제로 데이터 저장
        print(f"{len(texts)}개 문서를 벡터 저장소에 추가 중...")
        logger.info(f"{len(texts)}개 문서를 벡터 저장소에 추가 중...")
        
        # add_documents 메서드 호출
        # 이 메서드 안에서:
        # 1. 각 텍스트를 벡터(숫자 배열)로 변환 (임베딩 모델 사용)
        # 2. 벡터, 텍스트, 메타데이터, ID를 ChromaDB에 저장
        vectorstore.add_documents(texts=texts, metadatas=metadatas, ids=ids)
        
        # 저장 완료 메시지
        print(f"벡터 저장소 초기화 완료: {len(texts)}개 문서 저장")
        logger.info(f"벡터 저장소 초기화 완료: {len(texts)}개 문서 저장")
        
        # ===== 8단계: 테스트 검색 =====
        # 저장이 제대로 되었는지 테스트하기 위해 검색 실행
        test_query = "전주비빔밥"  # 검색할 키워드
        logger.info(f"테스트 검색 수행: '{test_query}'")
        
        # similarity_search: 벡터 유사도 검색
        # "전주비빔밥"과 유사한 메뉴를 찾음
        # k=3: 상위 3개 결과만 가져옴
        results = vectorstore.similarity_search(test_query, k=3)
        
        # 검색 결과 개수 로그 기록
        logger.info(f"테스트 검색 결과: {len(results)}개 결과")
        
        # 각 검색 결과를 하나씩 출력
        # enumerate(results, 1): 결과 리스트를 순회하면서 번호를 1부터 시작
        for i, result in enumerate(results, 1):
            # result는 딕셔너리 형태: {"content": "...", "metadata": {...}, "score": 0.95}
            # .get('menu_name', 'N/A'): metadata에서 menu_name 가져오기, 없으면 'N/A'
            # .get('score', 'N/A'): 유사도 점수 가져오기, 없으면 'N/A'
            # :.4f: 소수점 4자리까지 표시
            logger.info(f"  {i}. {result['metadata'].get('menu_name', 'N/A')} "
                       f"(점수: {result.get('score', 'N/A'):.4f})")
        
    except Exception as e:
        # 에러 발생 시 로그에 기록하고 다시 에러를 발생시킴
        # exc_info=True: 에러의 상세 정보(스택 트레이스)도 함께 기록
        logger.error(f"벡터 저장소 초기화 실패: {e}", exc_info=True)
        raise  # 에러를 다시 발생시켜서 프로그램이 멈추도록 함


# ===== 스크립트 실행 진입점 =====
# 이 파일을 직접 실행할 때만 아래 코드가 실행됨
# 다른 파일에서 import해서 사용할 때는 실행되지 않음
if __name__ == "__main__":
    # 메인 함수 호출: CSV 파일을 읽어서 벡터 DB에 저장하는 전체 프로세스 시작
    init_vectorstore_from_csv()