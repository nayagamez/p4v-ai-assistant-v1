"""
n8n Webhook 테스트 스크립트
사용법: python test_webhook.py
"""
import requests
import json

WEBHOOK_URL = 'https://n8n-nos.nmn.io/webhook-test/a1b46e74-9193-4f90-bc61-792e93c6ae0e'

payload = {
    'request_type': 'description',
    'changelist': {
        'number': 12345,
        'user': 'hong.gildong',
        'client': 'hong-pc-workspace',
        'current_description': '작업 중...'
    },
    'files': [
        {
            'depot_path': '//depot/MyProject/Source/Character/PlayerCharacter.cpp',
            'action': 'edit',
            'file_type': 'text',
            'revision': 15,
            'diff': '''--- a/PlayerCharacter.cpp
+++ b/PlayerCharacter.cpp
@@ -120,6 +120,15 @@
 void APlayerCharacter::BeginPlay()
 {
     Super::BeginPlay();
+
+    // 초기 체력 설정
+    CurrentHealth = MaxHealth;
+
+    // 스태미나 초기화
+    CurrentStamina = MaxStamina;
 }''',
            'content': ''
        },
        {
            'depot_path': '//depot/MyProject/Source/Character/PlayerCharacter.h',
            'action': 'edit',
            'file_type': 'text',
            'revision': 8,
            'diff': '''--- a/PlayerCharacter.h
+++ b/PlayerCharacter.h
@@ -45,6 +45,12 @@
     UPROPERTY(EditAnywhere)
     float MaxHealth = 100.0f;

+    UPROPERTY(VisibleAnywhere)
+    float CurrentHealth;
+
+    UPROPERTY(VisibleAnywhere)
+    float CurrentStamina;''',
            'content': ''
        }
    ]
}

def main():
    print('=' * 60)
    print('n8n Webhook Test')
    print('=' * 60)
    print(f'URL: {WEBHOOK_URL}')
    print()
    print('Sending request...')
    print()

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=120)
        print(f'Status Code: {response.status_code}')
        print()
        print('Response:')
        print('-' * 40)
        try:
            data = response.json()
            print(json.dumps(data, indent=2, ensure_ascii=False))
        except:
            print(response.text if response.text else '(empty response)')
        print('-' * 40)
    except requests.exceptions.Timeout:
        print('ERROR: Request timed out (120s)')
    except requests.exceptions.ConnectionError as e:
        print(f'ERROR: Connection failed - {e}')
    except Exception as e:
        print(f'ERROR: {e}')

if __name__ == '__main__':
    main()
