"""
백엔드 API 테스트 스크립트
"""

import requests
import json
import sys
import os
from typing import Dict, Any

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8000"
TIMEOUT = 60  # LLM 응답 대기 시간


def print_section(title: str):
    """섹션 제목 출력"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health():
    """헬스 체크 테스트"""
    print_section("1. 헬스 체크 테스트")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"[OK] Status Code: {response.status_code}")
        data = response.json()
        print(f"[OK] Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        return True
    except requests.exceptions.ConnectionError:
        print("[ERROR] 서버에 연결할 수 없습니다.")
        print("   서버를 먼저 실행하세요: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        return False


def test_root():
    """루트 엔드포인트 테스트"""
    print_section("2. 루트 엔드포인트 테스트")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        print(f"[OK] Status Code: {response.status_code}")
        data = response.json()
        print(f"[OK] API 정보:")
        print(f"   - 메시지: {data.get('message')}")
        print(f"   - 버전: {data.get('version')}")
        print(f"   - 엔드포인트: {', '.join(data.get('endpoints', {}).keys())}")
        return True
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        return False


def test_chat(message: str, description: str = ""):
    """채팅 테스트"""
    if description:
        print_section(f"3. 채팅 테스트: {description}")
    else:
        print_section(f"3. 채팅 테스트: '{message}'")
    
    try:
        payload = {
            "message": message
        }
        
        print(f"[요청] 메시지: {message}")
        print("[대기] 응답 대기 중... (LLM 처리 시간이 걸릴 수 있습니다)")
        
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        print(f"[OK] Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # 응답 내용
            response_text = data.get('response', '')
            print(f"\n[응답] 챗봇 응답:")
            print(f"   {response_text[:300]}{'...' if len(response_text) > 300 else ''}")
            
            # 추천 메뉴
            recommended_menus = data.get('recommended_menus', [])
            print(f"\n[추천] 추천 메뉴 수: {len(recommended_menus)}개")
            
            if recommended_menus:
                for i, menu in enumerate(recommended_menus[:5], 1):
                    print(f"\n   추천 {i}:")
                    print(f"      음식점: {menu.get('restaurant_name', 'N/A')}")
                    print(f"      메뉴: {menu.get('menu_name', 'N/A')}")
                    print(f"      가격: {menu.get('price', 'N/A')}원")
                    print(f"      칼로리: {menu.get('calories', 'N/A')}kcal")
                    print(f"      카테고리: {menu.get('category', 'N/A')}")
                    if menu.get('score'):
                        print(f"      유사도: {menu.get('score'):.4f}")
            else:
                print("   [WARNING] 추천 메뉴가 없습니다.")
            
            # 소스 정보
            sources = data.get('sources', [])
            print(f"\n[소스] 검색된 소스 수: {len(sources)}개")
            if sources:
                print(f"   첫 번째 소스 유사도: {sources[0].get('score', 0):.4f}")
            
            return True
        else:
            print(f"[ERROR] 오류 응답: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"[ERROR] 타임아웃: {TIMEOUT}초 내에 응답을 받지 못했습니다.")
        return False
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("  백엔드 API 테스트 시작")
    print("=" * 60)
    
    # 1. 헬스 체크
    if not test_health():
        print("\n[ERROR] 서버가 실행되지 않았습니다. 테스트를 중단합니다.")
        sys.exit(1)
    
    # 2. 루트 엔드포인트
    test_root()
    
    # 3. 다양한 채팅 테스트
    test_cases = [
        ("전주비빔밥 추천해줘", "기본 추천 테스트"),
        ("저렴한 한식 메뉴 추천해줘", "가격 필터링 테스트"),
        ("칼로리 낮은 메뉴 알려줘", "칼로리 필터링 테스트"),
    ]
    
    success_count = 0
    for message, description in test_cases:
        if test_chat(message, description):
            success_count += 1
        print()  # 빈 줄
    
    # 결과 요약
    print_section("테스트 결과 요약")
    print(f"[결과] 성공: {success_count}/{len(test_cases)}")
    if success_count == len(test_cases):
        print(f"[SUCCESS] 전체 테스트 성공!")
    else:
        print(f"[WARNING] 일부 테스트 실패")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
        sys.exit(0)

