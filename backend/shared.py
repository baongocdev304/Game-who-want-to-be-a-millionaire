"""
shared.py — Module trung tâm
Chứa: Flask app, tất cả imports, constants, db utilities, email utils.
Tất cả file route khác đều import từ đây.
"""

import os
import json
import random
import uuid
import time
import hashlib
import urllib.parse
import smtplib
import bcrypt
import psycopg2
import psycopg2.extras
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, g
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import get_connection, release_connection, create_schema

# ============================================================
# BIẾN MÔI TRƯỜNG
# ============================================================
load_dotenv()

# ============================================================
# GEMINI CLIENT
# ============================================================
try:
    api_key = os.environ.get('GEMINI_API_KEY')
    if api_key:
        gemini_client = genai.Client(api_key=api_key)
    else:
        gemini_client = None
        print("Canh bao: Khong tim thay GEMINI_API_KEY")
except Exception as e:
    gemini_client = None
    print(f"Loi khoi tao Gemini: {e}")

GEMINI_MODEL = 'models/gemini-flash-latest'

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__,
            static_folder='../static',
            template_folder='../templates')

app.secret_key = os.environ.get('SECRET_KEY', 'millionaire-secret-2026-xK9mP')
CORS(app, supports_credentials=True)

# ============================================================
# CONSTANTS
# ============================================================
PRIZE_LEVELS = [
    "200.000 d", "400.000 d", "600.000 d", "1.000.000 d", "2.000.000 d",
    "3.000.000 d", "6.000.000 d", "10.000.000 d", "14.000.000 d", "22.000.000 d",
    "30.000.000 d", "40.000.000 d", "60.000.000 d", "85.000.000 d", "150.000.000 d"
]
MILESTONES = [4, 9]
sessions = {}

# ============================================================
# SEPAY CONFIG
# ============================================================
def clean_env(val, default=""):
    if not val:
        return default
    val = str(val).split('#')[0]
    return val.strip()

SEPAY_BANK_CODE    = clean_env(os.environ.get('SEPAY_BANK_CODE'), 'MBBank')
SEPAY_ACCOUNT_NO   = clean_env(os.environ.get('SEPAY_ACCOUNT_NO'), '0123456789')
SEPAY_ACCOUNT_NAME = clean_env(os.environ.get('SEPAY_ACCOUNT_NAME'), 'AI LA TRIEU PHU')
WEBHOOK_SECRET     = clean_env(os.environ.get('WEBHOOK_SECRET'), 'dev-secret-123')

# ============================================================
# DATABASE UTILITIES
# ============================================================
def get_db():
    if 'db' not in g:
        g.db = get_connection()
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        release_connection(db)

def get_or_create_wallet(cur, user_id):
    cur.execute("SELECT game_turns, bonus_lifelines FROM user_wallets WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        return dict(row)
    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
    if not cur.fetchone():
        raise ValueError(f"User ID {user_id} khong ton tai.")
    cur.execute("""
        INSERT INTO user_wallets (user_id, game_turns, bonus_lifelines)
        VALUES (%s, 3, 0) ON CONFLICT (user_id) DO NOTHING
    """, (user_id,))
    return {'game_turns': 3, 'bonus_lifelines': 0}

def hash_password(pw):
    return bcrypt.hashpw(pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(pw, hashed):
    return bcrypt.checkpw(pw.encode('utf-8'), hashed.encode('utf-8'))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' not in session or 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Vui long dang nhap!'}), 401
            return redirect('/auth')
        user_id = session.get('user_id')
        conn = get_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
                    if not cur.fetchone():
                        session.clear()
                        if request.path.startswith('/api/'):
                            return jsonify({'success': False, 'error': 'Phien dang nhap het han!'}), 401
                        return redirect('/auth')
            except Exception:
                pass
        return f(*args, **kwargs)
    return decorated

# ============================================================
# EMAIL UTILITIES
# ============================================================
MAIL_SERVER   = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT     = int(os.environ.get('MAIL_PORT', 587))
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
MAIL_SENDER   = os.environ.get('MAIL_SENDER', 'Ai La Trieu Phu <support@millionaire.com>')

def send_email_code(receiver_email, code):
    print(f"\n[EMAIL] Gui toi {receiver_email}: Ma = {code}\n")
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        return True
    try:
        subject = "Ma xac nhan khoi phuc mat khau - Ai La Trieu Phu"
        body = f"Ma xac nhan cua ban la: {code}\nMa het han sau 15 phut."
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
        print(f"Loi gui email: {e}")
        return False
