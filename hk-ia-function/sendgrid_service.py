"""
SendGrid Email Service for HK Insurance AML System
使用 SendGrid API 發送郵件，替代 Gmail SMTP
"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
import logging

class SendGridEmailService:
    def __init__(self):
        """初始化 SendGrid 服務"""
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.from_email = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@hk-insurance-aml.com')
        self.client = None
        
        if self.api_key:
            self.client = SendGridAPIClient(api_key=self.api_key)
            print(f"SendGrid 初始化成功，發件人: {self.from_email}")
        else:
            print("⚠️  SendGrid API Key 未設定")
    
    def send_password_reset_email(self, to_email, new_password):
        """
        發送密碼重設郵件
        
        Args:
            to_email (str): 收件人信箱
            new_password (str): 新密碼
            
        Returns:
            dict: 發送結果
        """
        if not self.client:
            return {
                'success': False,
                'message': 'SendGrid 未正確配置'
            }
        
        try:
            # 建立郵件內容
            subject = "HK Insurance AML 系統 - 密碼重設通知"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>密碼重設通知</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #2c3e50; color: white; padding: 20px; text-align: center; }}
                    .content {{ background: #f9f9f9; padding: 30px; border-left: 4px solid #3498db; }}
                    .password {{ background: #e74c3c; color: white; padding: 15px; font-size: 18px; 
                               font-weight: bold; text-align: center; border-radius: 5px; margin: 20px 0; }}
                    .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
                    .warning {{ background: #f39c12; color: white; padding: 10px; border-radius: 5px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔐 HK Insurance AML 系統</h1>
                        <p>密碼重設通知</p>
                    </div>
                    
                    <div class="content">
                        <h2>您好！</h2>
                        <p>您的 HK Insurance AML 系統帳戶密碼已成功重設。</p>
                        
                        <div class="password">
                            新密碼：{new_password}
                        </div>
                        
                        <div class="warning">
                            ⚠️ 為了您的帳戶安全，請立即登入並更改為您個人專用的密碼。
                        </div>
                        
                        <p><strong>登入步驟：</strong></p>
                        <ol>
                            <li>訪問 HK Insurance AML 系統</li>
                            <li>使用您的信箱和上述新密碼登入</li>
                            <li>建議立即修改為您專用的密碼</li>
                        </ol>
                        
                        <p>如果您沒有要求重設密碼，請立即聯繫系統管理員。</p>
                    </div>
                    
                    <div class="footer">
                        <p>此郵件由 HK Insurance AML 系統自動發送，請勿回覆。</p>
                        <p>© 2025 HK Insurance AML System. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 純文字版本
            plain_content = f"""
HK Insurance AML 系統 - 密碼重設通知

您好！

您的 HK Insurance AML 系統帳戶密碼已成功重設。

新密碼：{new_password}

⚠️ 為了您的帳戶安全，請立即登入並更改為您個人專用的密碼。

登入步驟：
1. 訪問 HK Insurance AML 系統
2. 使用您的信箱和上述新密碼登入
3. 建議立即修改為您專用的密碼

如果您沒有要求重設密碼，請立即聯繫系統管理員。

此郵件由 HK Insurance AML 系統自動發送，請勿回覆。
© 2025 HK Insurance AML System. All rights reserved.
            """
            
            # 建立郵件
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content),
                plain_text_content=Content("text/plain", plain_content)
            )
            
            # 發送郵件
            response = self.client.send(message)
            
            if response.status_code in [200, 202]:
                return {
                    'success': True,
                    'message': 'Email 發送成功',
                    'status_code': response.status_code
                }
            else:
                return {
                    'success': False,
                    'message': f'Email 發送失敗，狀態碼: {response.status_code}',
                    'status_code': response.status_code
                }
                
        except Exception as e:
            error_msg = f"SendGrid 發送失敗: {str(e)}"
            print(error_msg)
            return {
                'success': False,
                'message': error_msg
            }
    
    def test_connection(self):
        """測試 SendGrid 連接"""
        if not self.client:
            return False
        
        try:
            # 嘗試獲取 API 狀態（這是一個輕量級測試）
            response = self.client.send(Mail(
                from_email=Email(self.from_email),
                to_emails=To("test@example.com"),
                subject="Test",
                html_content=Content("text/html", "<p>Test</p>")
            ), sandbox_mode=True)  # 沙盒模式，不會實際發送
            return True
        except Exception as e:
            print(f"SendGrid 連接測試失敗: {e}")
            return False

# 全域實例
sendgrid_service = SendGridEmailService()
