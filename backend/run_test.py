"""
서버 실행 및 테스트 통합 스크립트
"""

import subprocess
import time
import sys
import os
import requests

# Windows 콘솔 인코딩 설정
if sys.platform == 'win32':
    import codecs
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

def check_server_running():
    """서버가 실행 중인지 확인"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False

def wait_for_server(max_wait=30):
    """서버가 시작될 때까지 대기"""
    print("서버 시작 대기 중...")
    for i in range(max_wait):
        if check_server_running():
            print(f"[OK] 서버가 시작되었습니다! ({i+1}초)")
            return True
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print(f"   대기 중... ({i+1}초)")
    return False

def main():
    print("=" * 60)
    print("  백엔드 서버 실행 및 테스트")
    print("=" * 60)
    
    # 서버가 이미 실행 중인지 확인
    if check_server_running():
        print("[INFO] 서버가 이미 실행 중입니다.")
        print("[INFO] 테스트만 실행합니다.\n")
        # 테스트 스크립트 실행
        subprocess.run([sys.executable, "test_api.py"])
        return
    
    # 서버 실행
    print("\n[1단계] 서버 시작 중...")
    print("=" * 60)
    
    venv_python = os.path.join("venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        print("[ERROR] 가상환경을 찾을 수 없습니다.")
        print("   먼저 가상환경을 활성화하세요.")
        sys.exit(1)
    
    # 서버를 백그라운드로 실행
    server_process = subprocess.Popen(
        [venv_python, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.getcwd()
    )
    
    print(f"[INFO] 서버 프로세스 시작됨 (PID: {server_process.pid})")
    
    # 서버가 시작될 때까지 대기
    if not wait_for_server():
        print("[ERROR] 서버가 시작되지 않았습니다.")
        server_process.terminate()
        sys.exit(1)
    
    # 테스트 실행
    print("\n[2단계] API 테스트 실행")
    print("=" * 60)
    
    try:
        subprocess.run([sys.executable, "test_api.py"], check=True)
    except subprocess.CalledProcessError:
        print("\n[WARNING] 일부 테스트가 실패했습니다.")
    finally:
        # 서버 종료
        print("\n[3단계] 서버 종료")
        print("=" * 60)
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("[OK] 서버가 정상적으로 종료되었습니다.")
        except subprocess.TimeoutExpired:
            print("[WARNING] 서버 종료 대기 시간 초과. 강제 종료합니다.")
            server_process.kill()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
        sys.exit(0)




