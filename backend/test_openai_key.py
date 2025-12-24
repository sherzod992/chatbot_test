"""
OpenAI API 키 테스트 스크립트
"""

import sys
import os

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

def test_openai_api_key(api_key: str):
    """OpenAI API 키 테스트"""
    print("=" * 60)
    print("  OpenAI API 키 테스트")
    print("=" * 60)
    
    try:
        from openai import OpenAI
        
        print("\n[1단계] OpenAI 클라이언트 초기화 중...")
        client = OpenAI(api_key=api_key)
        
        print("[OK] 클라이언트 초기화 성공")
        
        # 간단한 테스트 호출
        print("\n[2단계] API 호출 테스트 중...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "안녕하세요. 한 문장으로 답변해주세요."}
            ],
            max_tokens=50
        )
        
        print(f"[OK] API 호출 성공!")
        print(f"[응답] {response.choices[0].message.content}")
        
        # 사용량 정보
        if hasattr(response, 'usage'):
            usage = response.usage
            print(f"\n[사용량]")
            print(f"  - 입력 토큰: {usage.prompt_tokens}")
            print(f"  - 출력 토큰: {usage.completion_tokens}")
            print(f"  - 총 토큰: {usage.total_tokens}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] API 테스트 실패")
        print(f"오류 내용: {error_msg[:300]}")
        
        # 오류 타입별 안내
        if "401" in error_msg or "invalid" in error_msg.lower() or "authentication" in error_msg.lower():
            print("\n[원인] API 키 인증 실패")
            print("  - API 키가 잘못되었거나")
            print("  - API 키가 비활성화되었습니다.")
            print("  - OpenAI Platform에서 새 API 키를 확인하세요.")
        elif "429" in error_msg or "rate limit" in error_msg.lower() or "quota" in error_msg.lower():
            print("\n[원인] 요청 제한 초과")
            print("  - 요청 제한에 도달했습니다.")
            print("  - 잠시 후 다시 시도하거나 OpenAI Platform에서 할당량을 확인하세요.")
        elif "insufficient_quota" in error_msg.lower():
            print("\n[원인] 크레딧 부족")
            print("  - 계정에 충분한 크레딧이 없습니다.")
            print("  - OpenAI Platform에서 결제 정보를 확인하세요.")
        
        return False


if __name__ == "__main__":
    # rag_chain.py에서 API 키 가져오기
    try:
        from app.rag_chain import OPENAI_API_KEY
        api_key = OPENAI_API_KEY
        print(f"[INFO] rag_chain.py에서 API 키를 가져왔습니다.")
    except Exception as e:
        print(f"[WARNING] rag_chain.py에서 API 키를 가져올 수 없습니다: {e}")
        # 직접 입력
        api_key = input("OpenAI API 키를 입력하세요: ").strip()
    
    success = test_openai_api_key(api_key)
    
    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] API 키가 정상적으로 작동합니다!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[FAILED] API 키 테스트 실패")
        print("=" * 60)
        sys.exit(1)

