"""
백엔드 API 테스트 스크립트
질문 → 벡터DB 검색 → LLM 응답 테스트
"""

import requests
import json
import sys
import time

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

BASE_URL = "http://localhost:8000"
TIMEOUT = 60


def test_chat(message: str):
    """질문 → 벡터DB → LLM 테스트
    
    Returns:
        tuple: (성공 여부, 응답 시간(초))
    """
    print("\n" + "=" * 60)
    print(f"  테스트: {message}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        payload = {"message": message}
        print(f"[질문] {message}")
        print("[처리] 벡터DB 검색 → LLM 응답 생성 중...")
        
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # LLM 응답
            response_text = data.get('response', '')
            print(f"\n[LLM 응답]")
            print(f"{response_text}")
            
            # 벡터DB 검색 결과
            sources = data.get('sources', [])
            print(f"\n[벡터DB 검색 결과] {len(sources)}개 문서 검색됨")
            if sources:
                print(f"   최고 유사도: {sources[0].get('score', 0):.4f}")
                print(f"   첫 번째 문서: {sources[0].get('content', '')[:100]}...")
            
            # 추천 메뉴 (벡터DB에서 검색된 결과)
            recommended_menus = data.get('recommended_menus', [])
            if recommended_menus:
                print(f"\n[추천 메뉴] {len(recommended_menus)}개")
                for i, menu in enumerate(recommended_menus[:3], 1):
                    print(f"   {i}. {menu.get('restaurant_name')} - {menu.get('menu_name')} ({menu.get('price')}원)")
            
            # 응답 시간
            print(f"\n[응답 시간] {response_time:.2f}초")
            
            return True, response_time
        else:
            end_time = time.time()
            response_time = end_time - start_time
            print(f"[ERROR] 오류 응답: {response.text}")
            return False, response_time
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] 서버에 연결할 수 없습니다.")
        print("   서버를 먼저 실행하세요: uvicorn app.main:app --reload")
        return False, 0
    except requests.exceptions.Timeout:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"[ERROR] 타임아웃: {TIMEOUT}초 내에 응답을 받지 못했습니다.")
        return False, elapsed_time
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"[ERROR] 오류: {e}")
        import traceback
        traceback.print_exc()
        return False, elapsed_time


def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 60)
    print("  질문 → 벡터DB → LLM 테스트")
    print("=" * 60)
    
    # 테스트 질문
    test_message = "점심 메뉴 추천해줘"
    
    # 테스트 실행
    success, response_time = test_chat(test_message)
    
    # 결과
    print("\n" + "=" * 60)
    if success:
        print(f"  ✅ 테스트 성공 (응답 시간: {response_time:.2f}초)")
    else:
        print(f"  ❌ 테스트 실패")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
        sys.exit(0)
