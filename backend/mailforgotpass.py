import os
import smtplib
from email.mime.text import MIMEText
from email.header import Header

MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')

MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '') # Nhập email của bạn vào .env
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '') # Nhập App Password vào .env
MAIL_SENDER = os.environ.get('MAIL_SENDER', 'Ai Là Triệu Phú Support <support@millionaire.com>')

def send_email_code(receiver_email, code):
    """Gửi mã xác nhận 6 số qua email."""
    subject = "Mã xác nhận khôi phục mật khẩu - Ai Là Triệu Phú"
    body = f"Chào bạn,\n\nMã xác nhận của bạn để đặt lại mật khẩu là: {code}\n\nMã này sẽ hết hạn sau 15 phút. Nếu không phải bạn yêu cầu, vui lòng bỏ qua email này."
    
    # In ra terminal để debug (nếu cấu hình email chưa chuẩn vẫn thấy mã)
    print(f"\n[EMAIL SIMULATION] Gửi tới {receiver_email}: Mã của bạn là {code}\n")
    
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        return True # Giả lập thành công

    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = MAIL_SENDER
        msg['To'] = receiver_email
        
        server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
        server.starttls()
        server.login(MAIL_USERNAME, MAIL_PASSWORD)
        server.sendmail(MAIL_USERNAME, receiver_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Lỗi gửi email: {e}")
        return False
