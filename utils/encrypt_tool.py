import os
import base64
import sys
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def get_cipher(master_key):
    """에이전트와 동일한 키 유도 로직"""
    salt = b'static_salt_for_now'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
    return Fernet(key)

def main():
    # 1. 마스터 키 확인 (.env 또는 직접 입력)
    master_key = os.getenv("MASTER_ENCRYPTION_KEY")
    if not master_key:
        print("❌ 에러: 환경 변수에 MASTER_ENCRYPTION_KEY가 없습니다.")
        master_key = input("사용하실 MASTER_ENCRYPTION_KEY를 입력하세요: ").strip()
        if not master_key:
            return

    cipher = get_cipher(master_key)

    print("\n--- 🔐 암호화 도구 ---")
    plain_text = input("암호화할 평문(예: GITHUB PAT)을 입력하세요: ").strip()
    
    if not plain_text:
        print("입력값이 없습니다.")
        return

    try:
        encrypted = cipher.encrypt(plain_text.encode()).decode()
        print("\n✅ 암호화 완료!")
        print(f"Supabase [key_value] 컬럼에 아래 값을 복사해서 넣으세요:")
        print("-" * 50)
        print(encrypted)
        print("-" * 50)
    except Exception as e:
        print(f"❌ 암호화 중 오류 발생: {e}")

if __name__ == "__main__":
    main()
