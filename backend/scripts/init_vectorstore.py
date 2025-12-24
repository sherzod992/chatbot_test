"""
벡터 DB 초기화 스크립트
음식점 메뉴 데이터를 벡터 DB에 저장

이 파일의 역할:
- ChromaDB 벡터 데이터베이스를 초기화하고 데이터를 로드
- MySQL에서 음식점 메뉴 데이터를 가져와 벡터로 변환하여 저장
- RAG 시스템이 사용할 검색 가능한 데이터를 준비

왜 필요한가:
- 애플리케이션 시작 전에 벡터 DB를 준비해야 함
- 음식점 메뉴 정보가 변경되면 벡터 DB도 업데이트 필요
- 배치 작업으로 대량의 데이터를 한 번에 처리
- 초기 설정 및 데이터 마이그레이션 시 사용

주요 기능:
- init_vectorstore(): 벡터 저장소 초기화 메인 함수
- format_restaurant_document(): 음식점 정보를 검색 가능한 텍스트로 변환
  - 음식점명, 주소, 설명, 카테고리, 메뉴 목록, 가격, 알레르기 정보, 영양 정보 포함

실행 흐름:
1. 기존 벡터 저장소 삭제 (초기화)
2. MySQL 데이터베이스에서 음식점 및 메뉴 데이터 조회
3. 데이터가 없으면 샘플 데이터 파일(sample_menu.json) 사용
4. 각 음식점 정보를 문서 형식으로 변환
5. 문서를 벡터로 변환하여 ChromaDB에 저장
6. 메타데이터(음식점 ID, 이름, 카테고리)와 함께 저장
7. 테스트 검색 수행하여 정상 작동 확인

언제 실행하나:
- 프로젝트 최초 설정 시
- 음식점/메뉴 데이터가 대량으로 변경되었을 때
- 벡터 DB가 손상되었을 때 재구축
- 정기적인 데이터 동기화 작업 (cron 등)

데이터 소스:
1. MySQL 데이터베이스 (우선순위)
   - restaurants 테이블
   - menus 테이블
2. 샘플 데이터 파일 (백업)
   - backend/data/sample_menu.json

사용 방법:
- python scripts/init_vectorstore.py
- 또는 스크립트로 실행
"""
"""
벡터 DB 초기화 스크립트
음식점 메뉴 데이터를 벡터 DB에 저장
"""

import sys
import csv
from pathlib import Path
from collections import defaultdict

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.vectorstore import VectorStore
from app.utils import logger


def format_restaurant_document(row):
    """CSV 행 데이터를 문서 형식으로 변환"""
    doc_parts = []
    
    # 음식점 기본 정보
    doc_parts.append(f"음식점명: {row['restaurant_name']}")
    doc_parts.append(f"주소: {row['address']}")
    doc_parts.append(f"카테고리: {row['category']}")
    
    # 메뉴 정보
    doc_parts.append(f"\n메뉴: {row['menu_name']}")
    doc_parts.append(f"가격: {row['price']}원")
    doc_parts.append(f"칼로리: {row['calories']}kcal")
    doc_parts.append(f"재료 원산지: {row['ingredients_origin']}")
    
    return "\n".join(doc_parts)


def load_csv_data(csv_path):
    """CSV 파일에서 데이터 로드"""
    restaurants = defaultdict(lambda: {"info": None, "menus": []})
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            restaurant_id = row['restaurant_id']
            
            # 음식점 정보 저장 (첫 번째 메뉴에서)
            if restaurants[restaurant_id]["info"] is None:
                restaurants[restaurant_id]["info"] = {
                    "restaurant_id": restaurant_id,
                    "restaurant_name": row['restaurant_name'],
                    "address": row['address'],
                    "category": row['category']
                }
            
            # 메뉴 정보 추가
            restaurants[restaurant_id]["menus"].append({
                "menu_id": row['menu_id'],
                "menu_name": row['menu_name'],
                "price": row['price'],
                "calories": row['calories'],
                "ingredients_origin": row['ingredients_origin']
            })
    
    return restaurants


def init_vectorstore_from_csv():
    """CSV 파일에서 벡터 저장소 초기화"""
    try:
        print("벡터 저장소 초기화 시작 (CSV 파일에서)")
        logger.info("벡터 저장소 초기화 시작 (CSV 파일에서)")
        
        # CSV 파일 경로
        csv_path = project_root / "data" / "restaurant_menu_data.csv"
        
        if not csv_path.exists():
            logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
            return
        
        # CSV 데이터 로드
        print(f"CSV 파일 로딩: {csv_path}")
        logger.info(f"CSV 파일 로딩: {csv_path}")
        restaurants = load_csv_data(csv_path)
        print(f"총 {len(restaurants)}개 음식점 데이터 로드 완료")
        logger.info(f"총 {len(restaurants)}개 음식점 데이터 로드 완료")
        
        # 기존 벡터 저장소 초기화 (선택적)
        vectorstore = VectorStore()
        try:
            vectorstore.delete_collection()
            logger.info("기존 컬렉션 삭제 완료")
        except:
            logger.info("기존 컬렉션이 없거나 삭제 불가")
        
        # 새 벡터 저장소 생성
        vectorstore = VectorStore()
        
        # 문서 및 메타데이터 준비
        texts = []
        metadatas = []
        ids = []
        
        for restaurant_id, data in restaurants.items():
            restaurant_info = data["info"]
            menus = data["menus"]
            
            # 각 메뉴마다 별도의 문서로 생성 (더 세밀한 검색을 위해)
            for menu in menus:
                # CSV 행 형태로 재구성
                row = {
                    **restaurant_info,
                    **menu
                }
                
                # 문서 텍스트 생성
                doc_text = format_restaurant_document(row)
                texts.append(doc_text)
                
                # 메타데이터 생성
                metadata = {
                    "restaurant_id": restaurant_info["restaurant_id"],
                    "restaurant_name": restaurant_info["restaurant_name"],
                    "address": restaurant_info["address"],
                    "category": restaurant_info["category"],
                    "menu_id": menu["menu_id"],
                    "menu_name": menu["menu_name"],
                    "price": menu["price"],
                    "calories": menu["calories"]
                }
                metadatas.append(metadata)
                
                # 고유 ID 생성
                ids.append(f"restaurant_{restaurant_id}_menu_{menu['menu_id']}")
        
        # 벡터 저장소에 추가
        print(f"{len(texts)}개 문서를 벡터 저장소에 추가 중...")
        logger.info(f"{len(texts)}개 문서를 벡터 저장소에 추가 중...")
        vectorstore.add_documents(texts=texts, metadatas=metadatas, ids=ids)
        
        print(f"벡터 저장소 초기화 완료: {len(texts)}개 문서 저장")
        logger.info(f"벡터 저장소 초기화 완료: {len(texts)}개 문서 저장")
        
        # 테스트 검색
        test_query = "전주비빔밥"
        logger.info(f"테스트 검색 수행: '{test_query}'")
        results = vectorstore.similarity_search(test_query, k=3)
        logger.info(f"테스트 검색 결과: {len(results)}개 결과")
        for i, result in enumerate(results, 1):
            logger.info(f"  {i}. {result['metadata'].get('menu_name', 'N/A')} "
                       f"(점수: {result.get('score', 'N/A'):.4f})")
        
    except Exception as e:
        logger.error(f"벡터 저장소 초기화 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    init_vectorstore_from_csv()