"""
==========================================
AI LA TRIEU PHU - BACKEND ENTRY POINT
==========================================
File: app.py
Mo ta: Diem khoi chay chinh. Import tat ca route modules tu cac file con.

Cau truc:
    shared.py      <- Flask app, constants, db utils, helpers
    app.py         <- Entry point, import tat ca routes
    register.py    <- POST /api/auth/register
    login.py       <- POST /api/auth/login, GET /api/auth/me, GET /, GET /auth
    logout.py      <- POST /api/auth/logout
    forgotpass.py  <- POST /api/auth/forgot-password, POST /api/auth/verify-reset-code
    QA.py          <- POST /api/game/answer + AI question generation
    session.py     <- POST /api/game/start + record_game_result
    supports.py    <- POST /api/game/lifeline
    stopped.py     <- POST /api/game/stop
    endtime.py     <- POST /api/game/timeout
    chatbot.py     <- POST /api/chatbot
    translate.py   <- POST /api/translate
    history.py     <- GET /api/game/history
    rank.py        <- GET /api/leaderboard
    shop.py        <- GET /api/shop/wallet, POST /api/shop/create-order, ...
    bank.py        <- POST /api/shop/webhook
    debug.py       <- GET /api/debug/status, ...
==========================================
"""

# === IMPORT FLASK APP & SHARED CODE ===
from shared import app, create_schema, get_connection

import sys
import os

# ==========================================
# IMPORT TAT CA ROUTE MODULES
# (Phai o cuoi file, sau khi app da duoc tao)
# ==========================================
import register       # POST /api/auth/register
import login          # POST /api/auth/login | GET /api/auth/me | GET / | GET /auth
import logout         # POST /api/auth/logout
import forgotpass     # POST /api/auth/forgot-password | POST /api/auth/verify-reset-code
import game_session   # POST /api/game/start  (file session.py doi ten thanh game_session.py)
import QA             # POST /api/game/answer
import supports       # POST /api/game/lifeline
import stopped        # POST /api/game/stop
import endtime        # POST /api/game/timeout
import chatbot        # POST /api/chatbot
import translate      # POST /api/translate
import history        # GET /api/game/history
import rank           # GET /api/leaderboard
import shop           # Shop routes
import bank           # POST /api/shop/webhook
import debug          # Debug routes

# === PWA ROUTES ===
from flask import send_from_directory

@app.route('/manifest.json')
def manifest():
    return send_from_directory('../static', 'manifest.json')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('../static', 'sw.js')

# === KHOI TAO DATABASE KHI KHOI DONG ===
try:
    with app.app_context():
        conn = get_connection()
        if conn:
            create_schema(conn)
            print("\n Database schema OK!")
        else:
            print("\n Khong the ket noi database!")
except Exception as db_err:
    print(f"\n Loi khoi tao database: {db_err}")

# === CHAY SERVER ===
if __name__ == '__main__':
    print("=" * 50)
    print("AI LA TRIEU PHU - SERVER")
    print("=" * 50)
    print(" Web:  http://localhost:5002")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5002, debug=True)
