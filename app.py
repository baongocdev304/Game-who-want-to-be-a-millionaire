"""
app.py (Root Entry Point)
===========================================================
File cầu nối giúp Render / Gunicorn / Docker tìm thấy ứng dụng Flask 
tại backend/app.py khi chạy từ thư mục gốc của repository.
"""
import os
import sys

# Thêm thư mục backend vào vị trí đầu tiên của sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_dir in sys.path:
    sys.path.remove(backend_dir)
sys.path.insert(0, backend_dir)

# Xóa 'app' khỏi sys.modules nếu nó đang trỏ vào root app.py
if 'app' in sys.modules and sys.modules['app'].__file__ == __file__:
    del sys.modules['app']

# Import WSGI app từ backend/app.py
import app as backend_app
app = backend_app.app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port)
