#!/usr/bin/env python3
"""
忘記密碼功能測試腳本
"""

import requests
import json

def test_forgot_password():
    """測試忘記密碼功能"""
    
    print("=== 忘記密碼功能測試 ===\n")
    
    # 測試案例
    test_cases = [
        {
            "email": "astcws@hotmail.com",
            "description": "有效的電子郵件"
        },
        {
            "email": "nonexistent@example.com", 
            "description": "不存在的電子郵件"
        },
        {
            "email": "",
            "description": "空的電子郵件"
        }
    ]
    
    base_url = "http://localhost:8090"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"測試 {i}: {test_case['description']}")
        print(f"Email: {test_case['email']}")
        
        try:
            response = requests.post(
                f"{base_url}/forgot-password",
                headers={"Content-Type": "application/json"},
                json={"email": test_case["email"]},
                timeout=10
            )
            
            print(f"狀態碼: {response.status_code}")
            
            try:
                result = response.json()
                print(f"回應: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success') and result.get('new_password'):
                    print(f"✅ 新密碼生成成功: {result['new_password']}")
                elif result.get('success'):
                    print("✅ 請求成功")
                else:
                    print(f"❌ 請求失敗: {result.get('message', '未知錯誤')}")
                    
            except json.JSONDecodeError:
                print(f"❌ 無法解析JSON回應: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 無法連接到服務器 {base_url}")
        except requests.exceptions.Timeout:
            print("❌ 請求超時")
        except Exception as e:
            print(f"❌ 發生錯誤: {str(e)}")
        
        print("-" * 50)

if __name__ == "__main__":
    test_forgot_password()
