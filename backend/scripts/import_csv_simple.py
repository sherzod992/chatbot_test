"""
CSV 파일을 벡터DB로 임포트하는 간단한 스크립트
chromadb 호환성 문제를 우회하기 위한 임시 솔루션
"""
# sys 모듈을 import합니다
# 왜? Python 인터프리터와 상호작용하기 위해 필요합니다 (경로 조작 등)
import sys
# csv 모듈을 import합니다
# 왜? CSV 파일을 읽고 파싱하기 위한 표준 라이브러리입니다
import csv
# json 모듈을 import합니다
# 왜? 데이터를 JSON 형식으로 저장하기 위해 필요합니다
import json
# pickle 모듈을 import합니다
# 왜? Python 객체를 직렬화하여 저장할 수 있지만, 이 스크립트에서는 실제로 사용하지 않습니다
import pickle
# Path 클래스를 pathlib 모듈에서 import합니다
# 왜? 파일 경로를 객체로 다루어 더 안전하고 직관적으로 경로를 조작할 수 있습니다
from pathlib import Path
# defaultdict를 collections 모듈에서 import합니다
# 왜? 딕셔너리의 키가 없을 때 자동으로 기본값을 생성해주어 코드를 간결하게 만듭니다
from collections import defaultdict

# 프로젝트 루트 디렉토리 경로를 계산합니다
# 왜? 현재 스크립트 파일의 위치를 기준으로 상위 디렉토리(프로젝트 루트)를 찾기 위해 필요합니다
project_root = Path(__file__).parent.parent

# 프로젝트 루트를 Python 경로(sys.path)의 맨 앞에 추가합니다
# 왜? 프로젝트 내의 다른 모듈(예: app.utils)을 import할 수 있도록 하기 위함입니다
sys.path.insert(0, str(project_root))
# app.utils 모듈에서 logger와 CHROMA_DB_PATH를 import합니다
# 왜? 로깅 기능과 벡터DB 저장 경로를 사용하기 위함입니다
from app.utils import logger, CHROMA_DB_PATH

# sentence-transformers와 numpy 라이브러리 import를 시도합니다
# 왜? 벡터화 작업에 필요하지만, 설치되지 않았을 수도 있으므로 try-except로 처리합니다
try:
    # SentenceTransformer 클래스를 import합니다
    # 왜? 텍스트를 벡터로 변환하는 임베딩 모델을 사용하기 위함입니다
    from sentence_transformers import SentenceTransformer
    # numpy 모듈을 import합니다
    # 왜? 벡터 데이터를 배열 형태로 저장하고 처리하기 위함입니다
    import numpy as np
    # HAS_TRANSFORMERS 플래그를 True로 설정합니다
    # 왜? 나중에 벡터화 기능을 사용할 수 있는지 확인하기 위한 플래그입니다
    HAS_TRANSFORMERS = True
# ImportError가 발생하면 (라이브러리가 설치되지 않은 경우)
# 왜? 필수가 아닌 선택적 라이브러리이므로, 없어도 스크립트는 동작해야 합니다
except ImportError:
    # HAS_TRANSFORMERS 플래그를 False로 설정합니다
    # 왜? 벡터화 기능을 사용할 수 없음을 표시합니다
    HAS_TRANSFORMERS = False
    # 경고 메시지를 로그에 기록합니다
    # 왜? 사용자에게 벡터화 기능이 비활성화되었음을 알리기 위함입니다
    logger.warning("sentence-transformers가 설치되지 않았습니다. 벡터화를 건너뜁니다.")


# format_restaurant_document 함수를 정의합니다
# 왜? CSV의 한 행(row) 데이터를 검색 가능한 텍스트 문서 형식으로 변환하기 위함입니다
def format_restaurant_document(row):
    """CSV 행 데이터를 문서 형식으로 변환"""
    # 빈 리스트를 생성합니다
    # 왜? 문서의 각 부분을 저장할 컨테이너가 필요합니다
    doc_parts = []
    
    # 음식점 기본 정보 섹션 시작을 표시하는 주석입니다
    # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
    
    # 음식점명을 포맷팅하여 리스트에 추가합니다
    # 왜? 검색 시 음식점명으로 찾을 수 있도록 문서에 포함시켜야 합니다
    doc_parts.append(f"음식점명: {row['restaurant_name']}")
    # 주소를 포맷팅하여 리스트에 추가합니다
    # 왜? 위치 기반 검색이나 주소 정보 제공을 위해 필요합니다
    doc_parts.append(f"주소: {row['address']}")
    # 카테고리를 포맷팅하여 리스트에 추가합니다
    # 왜? 음식 종류별 필터링이나 검색을 위해 필요합니다
    doc_parts.append(f"카테고리: {row['category']}")
    
    # 메뉴 정보 섹션 시작을 표시하는 주석입니다
    # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
    
    # 메뉴명을 포맷팅하여 리스트에 추가합니다 (앞에 줄바꿈 추가)
    # 왜? 음식점 정보와 메뉴 정보를 시각적으로 구분하기 위함입니다
    doc_parts.append(f"\n메뉴: {row['menu_name']}")
    # 가격을 포맷팅하여 리스트에 추가합니다
    # 왜? 가격 기반 검색이나 필터링을 위해 필요합니다
    doc_parts.append(f"가격: {row['price']}원")
    # 칼로리를 포맷팅하여 리스트에 추가합니다
    # 왜? 건강 정보 기반 검색이나 필터링을 위해 필요합니다
    doc_parts.append(f"칼로리: {row['calories']}kcal")
    # 재료 원산지를 포맷팅하여 리스트에 추가합니다
    # 왜? 원산지 정보는 사용자가 중요하게 생각할 수 있는 정보이기 때문입니다
    doc_parts.append(f"재료 원산지: {row['ingredients_origin']}")
    
    # 리스트의 모든 요소를 줄바꿈 문자로 연결하여 하나의 문자열로 반환합니다
    # 왜? 벡터화 작업은 문자열 형태의 텍스트가 필요하기 때문입니다
    return "\n".join(doc_parts)


# load_csv_data 함수를 정의합니다
# 왜? CSV 파일에서 데이터를 읽어서 구조화된 형태로 변환하기 위함입니다
def load_csv_data(csv_path):
    """CSV 파일에서 데이터 로드"""
    # defaultdict를 사용하여 음식점별로 데이터를 그룹화할 딕셔너리를 생성합니다
    # 왜? 같은 음식점의 여러 메뉴를 하나로 묶어서 관리하기 위함입니다
    restaurants = defaultdict(lambda: {"info": None, "menus": []})
    
    # CSV 파일을 읽기 모드로 엽니다 (UTF-8-SIG 인코딩 사용)
    # 왜? UTF-8-SIG는 BOM(Byte Order Mark)을 처리하여 Excel에서 저장한 CSV 파일도 올바르게 읽을 수 있습니다
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        # CSV 파일을 딕셔너리 형태로 읽는 리더를 생성합니다
        # 왜? 각 행을 딕셔너리로 변환하면 컬럼명으로 데이터에 접근할 수 있어 편리합니다
        reader = csv.DictReader(f)
        # CSV의 각 행을 순회합니다
        # 왜? 모든 데이터를 처리하기 위해 반복문이 필요합니다
        for row in reader:
            # 현재 행의 restaurant_id를 변수에 저장합니다
            # 왜? 음식점별로 데이터를 그룹화하기 위한 키로 사용합니다
            restaurant_id = row['restaurant_id']
            
            # 음식점 정보가 아직 저장되지 않았는지 확인합니다
            # 왜? 같은 음식점의 여러 메뉴가 있지만, 음식점 정보는 한 번만 저장하면 되기 때문입니다
            if restaurants[restaurant_id]["info"] is None:
                # 음식점 기본 정보를 딕셔너리 형태로 저장합니다
                # 왜? 음식점 정보를 구조화하여 나중에 쉽게 접근할 수 있도록 하기 위함입니다
                restaurants[restaurant_id]["info"] = {
                    # 음식점 ID를 저장합니다
                    # 왜? 고유 식별자로 사용하기 위함입니다
                    "restaurant_id": restaurant_id,
                    # 음식점명을 저장합니다
                    # 왜? 사용자에게 표시하거나 검색에 사용하기 위함입니다
                    "restaurant_name": row['restaurant_name'],
                    # 주소를 저장합니다
                    # 왜? 위치 정보 제공을 위해 필요합니다
                    "address": row['address'],
                    # 카테고리를 저장합니다
                    # 왜? 음식 종류별 분류를 위해 필요합니다
                    "category": row['category']
                }
            
            # 메뉴 정보 섹션 시작을 표시하는 주석입니다
            # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
            
            # 현재 행의 메뉴 정보를 해당 음식점의 메뉴 리스트에 추가합니다
            # 왜? 하나의 음식점에 여러 메뉴가 있을 수 있으므로 리스트로 관리해야 합니다
            restaurants[restaurant_id]["menus"].append({
                # 메뉴 ID를 저장합니다
                # 왜? 각 메뉴를 고유하게 식별하기 위함입니다
                "menu_id": row['menu_id'],
                # 메뉴명을 저장합니다
                # 왜? 사용자에게 표시하거나 검색에 사용하기 위함입니다
                "menu_name": row['menu_name'],
                # 가격을 저장합니다
                # 왜? 가격 정보는 검색과 필터링에 중요한 요소입니다
                "price": row['price'],
                # 칼로리를 저장합니다
                # 왜? 건강 정보는 많은 사용자가 관심을 가지는 정보입니다
                "calories": row['calories'],
                # 재료 원산지를 저장합니다
                # 왜? 식품 안전과 품질에 대한 정보를 제공하기 위함입니다
                "ingredients_origin": row['ingredients_origin']
            })
    
    # 처리된 음식점 데이터를 반환합니다
    # 왜? 이 함수를 호출한 곳에서 구조화된 데이터를 사용할 수 있도록 하기 위함입니다
    return restaurants


# save_to_simple_vectorstore 함수를 정의합니다
# 왜? 처리된 문서, 메타데이터, 벡터를 파일로 저장하기 위함입니다
def save_to_simple_vectorstore(documents, metadatas, embeddings, output_dir):
    """간단한 벡터 저장소에 저장"""
    # output_dir을 Path 객체로 변환합니다
    # 왜? Path 객체를 사용하면 경로 조작이 더 안전하고 편리합니다
    output_dir = Path(output_dir)
    # 출력 디렉토리가 없으면 생성합니다 (exist_ok=True는 이미 존재해도 에러를 발생시키지 않음)
    # 왜? 저장하기 전에 디렉토리가 존재해야 파일을 저장할 수 있기 때문입니다
    output_dir.mkdir(exist_ok=True)
    
    # 문서 저장 섹션 시작을 표시하는 주석입니다
    # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
    
    # documents.json 파일을 쓰기 모드로 엽니다
    # 왜? 문서 텍스트들을 JSON 형식으로 저장하기 위함입니다
    with open(output_dir / "documents.json", 'w', encoding='utf-8') as f:
        # documents 리스트를 JSON 형식으로 파일에 저장합니다
        # 왜? JSON은 사람이 읽을 수 있고 다른 프로그램에서도 쉽게 파싱할 수 있는 형식입니다
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    # 메타데이터 저장 섹션 시작을 표시하는 주석입니다
    # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
    
    # metadatas.json 파일을 쓰기 모드로 엽니다
    # 왜? 메타데이터를 JSON 형식으로 저장하기 위함입니다
    with open(output_dir / "metadatas.json", 'w', encoding='utf-8') as f:
        # metadatas 리스트를 JSON 형식으로 파일에 저장합니다
        # 왜? 메타데이터도 나중에 검색이나 필터링에 사용할 수 있도록 저장해야 합니다
        json.dump(metadatas, f, ensure_ascii=False, indent=2)
    
    # 벡터 저장 섹션 시작을 표시하는 주석입니다
    # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
    
    # embeddings가 None이 아닌지 확인합니다
    # 왜? 벡터화가 선택적 기능이므로, 벡터가 있을 때만 저장해야 합니다
    if embeddings is not None:
        # numpy 배열을 .npy 파일로 저장합니다
        # 왜? numpy 배열은 대용량 데이터를 효율적으로 저장하고 로드할 수 있는 바이너리 형식입니다
        np.save(output_dir / "embeddings.npy", np.array(embeddings))
    
    # 저장 완료 메시지를 로그에 기록합니다
    # 왜? 작업이 성공적으로 완료되었음을 확인하고 디버깅에 도움이 됩니다
    logger.info(f"데이터 저장 완료: {output_dir}")


# import_csv_to_vectorstore 함수를 정의합니다
# 왜? 전체 CSV 임포트 프로세스를 관리하는 메인 함수입니다
def import_csv_to_vectorstore():
    """CSV 파일에서 벡터 저장소로 임포트"""
    # try-except 블록을 시작합니다
    # 왜? 오류가 발생해도 프로그램이 중단되지 않고 적절한 오류 메시지를 출력하기 위함입니다
    try:
        # 구분선을 출력합니다 (60개의 '=' 문자)
        # 왜? 콘솔 출력을 보기 좋게 정리하고 작업 시작을 명확히 표시하기 위함입니다
        print("=" * 60)
        # 작업 시작 메시지를 출력합니다
        # 왜? 사용자에게 현재 진행 중인 작업을 알리기 위함입니다
        print("CSV 파일을 벡터DB로 임포트 시작")
        # 구분선을 출력합니다
        # 왜? 메시지의 시작과 끝을 명확히 구분하기 위함입니다
        print("=" * 60)
        
        # CSV 파일 경로 섹션 시작을 표시하는 주석입니다
        # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
        
        # CSV 파일의 전체 경로를 생성합니다
        # 왜? 프로젝트 루트의 data 폴더에 있는 CSV 파일을 찾기 위함입니다
        csv_path = project_root / "data" / "restaurant_menu_data.csv"
        
        # CSV 파일이 존재하는지 확인합니다
        # 왜? 파일이 없으면 작업을 진행할 수 없으므로 미리 확인해야 합니다
        if not csv_path.exists():
            # 파일이 없을 때 에러 메시지를 로그에 기록합니다
            # 왜? 문제를 진단하고 해결하는 데 도움이 됩니다
            logger.error(f"CSV 파일을 찾을 수 없습니다: {csv_path}")
            # 함수를 종료합니다
            # 왜? 파일이 없으면 더 이상 진행할 수 없으므로 함수를 종료해야 합니다
            return
        
        # CSV 데이터 로드 섹션 시작을 표시하는 주석입니다
        # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
        
        # CSV 파일 로딩 메시지를 출력합니다
        # 왜? 사용자에게 현재 진행 상황을 알리기 위함입니다
        print(f"\nCSV 파일 로딩: {csv_path}")
        # load_csv_data 함수를 호출하여 CSV 데이터를 로드합니다
        # 왜? 구조화된 데이터가 필요하므로 변환 함수를 사용합니다
        restaurants = load_csv_data(csv_path)
        # 로드 완료 메시지와 함께 음식점 개수를 출력합니다
        # 왜? 사용자에게 처리된 데이터의 양을 알려주기 위함입니다
        print(f"총 {len(restaurants)}개 음식점 데이터 로드 완료")
        
        # 문서 및 메타데이터 준비 섹션 시작을 표시하는 주석입니다
        # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
        
        # 문서 텍스트를 저장할 빈 리스트를 생성합니다
        # 왜? 각 메뉴별로 생성된 문서를 모아서 저장하기 위함입니다
        documents = []
        # 메타데이터를 저장할 빈 리스트를 생성합니다
        # 왜? 각 문서에 대한 추가 정보를 저장하기 위함입니다
        metadatas = []
        # 문서 ID를 저장할 빈 리스트를 생성합니다
        # 왜? 각 문서를 고유하게 식별하기 위한 ID가 필요합니다
        ids = []
        
        # restaurants 딕셔너리의 각 항목을 순회합니다
        # 왜? 모든 음식점의 데이터를 처리해야 하기 때문입니다
        for restaurant_id, data in restaurants.items():
            # 현재 음식점의 기본 정보를 변수에 저장합니다
            # 왜? 반복적으로 접근하므로 변수에 저장하면 코드가 간결해집니다
            restaurant_info = data["info"]
            # 현재 음식점의 메뉴 리스트를 변수에 저장합니다
            # 왜? 각 메뉴를 개별 문서로 만들기 위해 메뉴 리스트가 필요합니다
            menus = data["menus"]
            
            # 각 메뉴마다 별도의 문서로 생성한다는 주석입니다
            # 왜? 더 세밀한 검색을 위해 각 메뉴를 독립적인 문서로 만듭니다
            
            # 메뉴 리스트의 각 메뉴를 순회합니다
            # 왜? 각 메뉴마다 문서를 생성해야 하기 때문입니다
            for menu in menus:
                # CSV 행 형태로 재구성한다는 주석입니다
                # 왜? format_restaurant_document 함수가 기대하는 형식으로 데이터를 구성합니다
                
                # 음식점 정보와 메뉴 정보를 하나의 딕셔너리로 합칩니다
                # 왜? format_restaurant_document 함수가 모든 정보를 한 곳에서 접근할 수 있어야 하기 때문입니다
                row = {
                    # 딕셔너리 언패킹을 사용하여 restaurant_info의 모든 키-값을 포함합니다
                    # 왜? 코드를 간결하게 만들고 모든 정보를 쉽게 전달할 수 있습니다
                    **restaurant_info,
                    # 딕셔너리 언패킹을 사용하여 menu의 모든 키-값을 포함합니다
                    # 왜? 메뉴 정보도 함께 포함시켜야 하기 때문입니다
                    **menu
                }
                
                # 문서 텍스트 생성 섹션 시작을 표시하는 주석입니다
                # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
                
                # format_restaurant_document 함수를 호출하여 문서 텍스트를 생성합니다
                # 왜? 검색 가능한 텍스트 형식으로 변환해야 벡터화할 수 있습니다
                doc_text = format_restaurant_document(row)
                # 생성된 문서 텍스트를 documents 리스트에 추가합니다
                # 왜? 나중에 벡터화하고 저장하기 위해 모아둬야 합니다
                documents.append(doc_text)
                
                # 메타데이터 생성 섹션 시작을 표시하는 주석입니다
                # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
                
                # 메타데이터 딕셔너리를 생성합니다
                # 왜? 검색 결과에서 추가 정보를 제공하거나 필터링에 사용하기 위함입니다
                metadata = {
                    # 음식점 ID를 메타데이터에 포함합니다
                    # 왜? 검색 결과를 음식점별로 그룹화하거나 필터링할 때 필요합니다
                    "restaurant_id": restaurant_info["restaurant_id"],
                    # 음식점명을 메타데이터에 포함합니다
                    # 왜? 검색 결과에 표시할 정보이기 때문입니다
                    "restaurant_name": restaurant_info["restaurant_name"],
                    # 주소를 메타데이터에 포함합니다
                    # 왜? 위치 정보는 사용자에게 중요한 정보입니다
                    "address": restaurant_info["address"],
                    # 카테고리를 메타데이터에 포함합니다
                    # 왜? 카테고리별 필터링에 필요합니다
                    "category": restaurant_info["category"],
                    # 메뉴 ID를 메타데이터에 포함합니다
                    # 왜? 각 메뉴를 고유하게 식별하기 위함입니다
                    "menu_id": menu["menu_id"],
                    # 메뉴명을 메타데이터에 포함합니다
                    # 왜? 검색 결과에 표시할 정보이기 때문입니다
                    "menu_name": menu["menu_name"],
                    # 가격을 메타데이터에 포함합니다
                    # 왜? 가격 기반 필터링이나 정렬에 필요합니다
                    "price": menu["price"],
                    # 칼로리를 메타데이터에 포함합니다
                    # 왜? 칼로리 기반 필터링에 필요합니다
                    "calories": menu["calories"]
                }
                # 생성된 메타데이터를 metadatas 리스트에 추가합니다
                # 왜? documents와 같은 순서로 저장하여 나중에 매칭할 수 있도록 해야 합니다
                metadatas.append(metadata)
                
                # 고유 ID 생성 섹션 시작을 표시하는 주석입니다
                # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
                
                # 음식점 ID와 메뉴 ID를 조합하여 고유 ID를 생성합니다
                # 왜? 각 문서를 고유하게 식별할 수 있어야 나중에 검색 결과를 정확히 매칭할 수 있습니다
                ids.append(f"restaurant_{restaurant_id}_menu_{menu['menu_id']}")
        
        # 생성된 문서 개수를 출력합니다
        # 왜? 사용자에게 처리된 문서의 수를 알려주기 위함입니다
        print(f"\n총 {len(documents)}개 문서 생성 완료")
        
        # 벡터화 섹션 시작을 표시하는 주석입니다
        # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
        
        # embeddings 변수를 None으로 초기화합니다
        # 왜? 벡터화가 실패하거나 건너뛸 경우를 대비하여 초기값을 설정합니다
        embeddings = None
        # HAS_TRANSFORMERS 플래그를 확인합니다
        # 왜? sentence-transformers 라이브러리가 설치되어 있는지 확인해야 벡터화를 진행할 수 있습니다
        if HAS_TRANSFORMERS:
            # 벡터화 시작 메시지를 출력합니다
            # 왜? 사용자에게 시간이 걸리는 작업이 시작되었음을 알리기 위함입니다
            print("\n벡터화 시작...")
            # 모델 로딩 메시지를 출력합니다
            # 왜? 처음 실행 시 모델 다운로드로 인해 시간이 걸릴 수 있음을 사용자에게 알리기 위함입니다
            print("임베딩 모델 로딩 중... (처음 실행 시 시간이 걸릴 수 있습니다)")
            # 한국어 전용 임베딩 모델을 로드합니다
            # 왜? 한국어 텍스트를 벡터로 변환하기 위해 한국어에 최적화된 모델이 필요합니다
            model = SentenceTransformer('jhgan/ko-sroberta-multitask')
            
            # 문서 개수와 함께 벡터 변환 시작 메시지를 출력합니다
            # 왜? 사용자에게 진행 상황을 알리기 위함입니다
            print(f"{len(documents)}개 문서를 벡터로 변환 중...")
            # 모든 문서를 벡터로 변환합니다 (정규화 적용, 진행률 표시)
            # 왜? 벡터 검색을 위해서는 텍스트를 숫자 벡터로 변환해야 하며, 정규화는 검색 성능을 향상시킵니다
            embeddings = model.encode(documents, normalize_embeddings=True, show_progress_bar=True)
            # 벡터화 완료 메시지를 출력합니다
            # 왜? 작업이 성공적으로 완료되었음을 사용자에게 알리기 위함입니다
            print("벡터화 완료!")
        else:
            # 벡터화를 건너뛴다는 메시지를 출력합니다
            # 왜? 필수 라이브러리가 없어서 벡터화를 할 수 없음을 사용자에게 알리기 위함입니다
            print("\n벡터화를 건너뜁니다 (sentence-transformers 미설치)")
        
        # 벡터 저장소에 저장 섹션 시작을 표시하는 주석입니다
        # 왜? 코드의 가독성을 높이고 각 섹션을 구분하기 위함입니다
        
        # 벡터 저장소의 출력 디렉토리 경로를 생성합니다
        # 왜? 저장할 위치를 지정해야 합니다
        output_dir = CHROMA_DB_PATH / "simple_store"
        # save_to_simple_vectorstore 함수를 호출하여 데이터를 저장합니다
        # 왜? 처리된 모든 데이터를 파일로 저장하여 나중에 사용할 수 있도록 해야 합니다
        save_to_simple_vectorstore(documents, metadatas, embeddings, output_dir)
        
        # 구분선을 출력합니다
        # 왜? 작업 완료 섹션을 명확히 구분하기 위함입니다
        print("\n" + "=" * 60)
        # 임포트 완료 메시지를 출력합니다
        # 왜? 사용자에게 작업이 성공적으로 완료되었음을 알리기 위함입니다
        print(f"임포트 완료!")
        # 저장된 문서 수를 출력합니다
        # 왜? 사용자에게 처리된 데이터의 양을 알려주기 위함입니다
        print(f"- 문서 수: {len(documents)}개")
        # 저장 위치를 출력합니다
        # 왜? 사용자가 저장된 파일의 위치를 알 수 있도록 하기 위함입니다
        print(f"- 저장 위치: {output_dir}")
        # embeddings가 None이 아닌 경우에만 실행됩니다
        # 왜? 벡터가 생성되었을 때만 차원 정보를 표시할 수 있습니다
        if embeddings is not None:
            # 벡터의 차원 수를 출력합니다 (shape 속성이 있는 경우)
            # 왜? 벡터의 차원은 검색 성능과 저장 공간에 영향을 주는 중요한 정보입니다
            print(f"- 벡터 차원: {embeddings.shape[1] if hasattr(embeddings, 'shape') else 'N/A'}")
        # 구분선을 출력합니다
        # 왜? 작업 완료 섹션의 끝을 명확히 표시하기 위함입니다
        print("=" * 60)
        
    # 예외가 발생했을 때 처리하는 블록입니다
    # 왜? 오류가 발생해도 프로그램이 갑자기 종료되지 않고 적절한 오류 처리를 할 수 있습니다
    except Exception as e:
        # 오류 메시지를 로그에 기록합니다 (상세한 스택 트레이스 포함)
        # 왜? 문제를 진단하고 해결하는 데 필요한 정보를 제공하기 위함입니다
        logger.error(f"임포트 실패: {e}", exc_info=True)
        # 예외를 다시 발생시킵니다
        # 왜? 호출한 곳에서도 오류를 처리할 수 있도록 하기 위함입니다
        raise


# 이 스크립트가 직접 실행될 때만 실행되는 코드 블록입니다
# 왜? 다른 파일에서 import할 때는 실행되지 않고, 직접 실행할 때만 함수를 호출하기 위함입니다
if __name__ == "__main__":
    # import_csv_to_vectorstore 함수를 호출합니다
    # 왜? 스크립트를 직접 실행하면 CSV 임포트 작업을 시작하기 위함입니다
    import_csv_to_vectorstore()
