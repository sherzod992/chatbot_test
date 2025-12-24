"""
CSV 파일을 벡터DB로 임포트하는 간단한 스크립트
chromadb 호환성 문제를 우회하기 위한 임시 솔루션
"""
import sys
import csv
import json
import pickle
from pathlib import Path
from collections import defaultdict

# 프로젝트 루트를 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils import logger, CHROMA_DB_PATH

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("sentence-transformers가 설치되지 않았습니다. 벡터화를 건너뜁니다.")


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


def save_to_simple_vectorstore(documents, metadatas, embeddings, output_dir):
    """간단한 벡터 저장소에 저장"""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 문서 저장
    with open(output_dir / "documents.json", 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    # 메타데이터 저장
    with open(output_dir / "metadatas.json", 'w', encoding='utf-8') as f:
        json.dump(metadatas, f, ensure_ascii=False, indent=2)
    
    # 벡터 저장 (numpy 배열)
    if embeddings is not None:
        np.save(output_dir / "embeddings.npy", np.array(embeddings))
    
    logger.info(f"데이터 저장 완료: {output_dir}")


def import_csv_to_vectorstore():
    """CSV 파일에서 벡터 저장소로 임포트"""
    try:
        print("=" * 60)
        print("CSV 파일을 벡터DB로 임포트 시작")
        print("=" * 60)
        
        # CSV 파일 경로
        csv_path = project_root / "data" / "restaurant_menu_data.csv"
        
        if not csv_path.exists():
            logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
            return
        
        # CSV 데이터 로드
        print(f"\nCSV 파일 로딩: {csv_path}")
        restaurants = load_csv_data(csv_path)
        print(f"총 {len(restaurants)}개 음식점 데이터 로드 완료")
        
        # 문서 및 메타데이터 준비
        documents = []
        metadatas = []
        ids = []
        
        for restaurant_id, data in restaurants.items():
            restaurant_info = data["info"]
            menus = data["menus"]
            
            # 각 메뉴마다 별도의 문서로 생성
            for menu in menus:
                # CSV 행 형태로 재구성
                row = {
                    **restaurant_info,
                    **menu
                }
                
                # 문서 텍스트 생성
                doc_text = format_restaurant_document(row)
                documents.append(doc_text)
                
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
        
        print(f"\n총 {len(documents)}개 문서 생성 완료")
        
        # 벡터화 (선택적)
        embeddings = None
        if HAS_TRANSFORMERS:
            print("\n벡터화 시작...")
            print("임베딩 모델 로딩 중... (처음 실행 시 시간이 걸릴 수 있습니다)")
            model = SentenceTransformer('jhgan/ko-sroberta-multitask')
            
            print(f"{len(documents)}개 문서를 벡터로 변환 중...")
            embeddings = model.encode(documents, normalize_embeddings=True, show_progress_bar=True)
            print("벡터화 완료!")
        else:
            print("\n벡터화를 건너뜁니다 (sentence-transformers 미설치)")
        
        # 벡터 저장소에 저장
        output_dir = CHROMA_DB_PATH / "simple_store"
        save_to_simple_vectorstore(documents, metadatas, embeddings, output_dir)
        
        print("\n" + "=" * 60)
        print(f"임포트 완료!")
        print(f"- 문서 수: {len(documents)}개")
        print(f"- 저장 위치: {output_dir}")
        if embeddings is not None:
            print(f"- 벡터 차원: {embeddings.shape[1] if hasattr(embeddings, 'shape') else 'N/A'}")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"임포트 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import_csv_to_vectorstore()

