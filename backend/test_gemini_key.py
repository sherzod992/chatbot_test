"""
Gemini API 키 테스트 스크립트
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

def test_gemini_api_key(api_key: str):
    """Gemini API 키 테스트"""
    print("=" * 60)
    print("  Gemini API 키 테스트")
    print("=" * 60)
    
    try:
        # google.generativeai 사용
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        print("\n[1단계] 사용 가능한 모델 확인 중...")
        models = genai.list_models()
        available_models = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name.replace('models/', ''))
        
        print(f"[OK] 사용 가능한 모델: {', '.join(available_models[:5])}")
        
        # 간단한 테스트 호출
        print("\n[2단계] API 호출 테스트 중...")
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("안녕하세요. 한 문장으로 답변해주세요.")
        
        print(f"[OK] API 호출 성공!")
        print(f"[응답] {response.text[:100]}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] API 테스트 실패")
        print(f"오류 내용: {error_msg[:300]}")
        
        # 오류 타입별 안내
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            print("\n[원인] 할당량 초과")
            print("  - 무료 티어 할당량을 모두 사용했거나")
            print("  - 요청 제한에 도달했습니다.")
            print("  - 잠시 후 다시 시도하거나 Google AI Studio에서 할당량을 확인하세요.")
        elif "401" in error_msg or "UNAUTHENTICATED" in error_msg or "invalid" in error_msg.lower():
            print("\n[원인] API 키 인증 실패")
            print("  - API 키가 잘못되었거나")
            print("  - API 키가 비활성화되었습니다.")
            print("  - Google AI Studio에서 새 API 키를 생성하세요.")
        elif "404" in error_msg or "NOT_FOUND" in error_msg:
            print("\n[원인] 모델을 찾을 수 없음")
            print("  - 모델 이름이 잘못되었거나")
            print("  - 해당 모델이 사용 불가능합니다.")
        
        return False


if __name__ == "__main__":
    # 환경 변수에서 API 키 가져오기
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print(f"[WARNING] 환경 변수 GEMINI_API_KEY를 찾을 수 없습니다.")
        # 직접 입력
        api_key = input("Gemini API 키를 입력하세요: ").strip()
    else:
        print(f"[INFO] 환경 변수에서 API 키를 가져왔습니다.")
    
    success = test_gemini_api_key(api_key)
    
    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] API 키가 정상적으로 작동합니다!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("[FAILED] API 키 테스트 실패")
        print("=" * 60)
        sys.exit(1)

