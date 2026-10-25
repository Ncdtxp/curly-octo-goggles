"""
Tap Sim Reborn — Web Version (Flask Backend)
"""

from __future__ import annotations

import os
import random
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "tap_sim_reborn_secret_key_change_this"
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            tokens INTEGER DEFAULT 1000,
            wagered INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user(user_id: int, username: str = "Player"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tokens, wagered FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, username, tokens, wagered) VALUES (?, ?, 1000, 0)", (user_id, username))
        conn.commit()
        tokens, wagered = 1000, 0
    else:
        tokens, wagered = row[0], row[1]
    conn.close()
    return tokens, wagered

@app.route("/", methods=["GET", "POST"])
def index():
    # Test için geçici bir user_id (Gerçek sistemde Roblox OAuth veya basit ID olacak)
    user_id = session.get("user_id", 12345)
    username = session.get("username", "Oyuncu")
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "login":
            entered_name = request.form.get("username", "").strip()
            if entered_name:
                session["username"] = entered_name
                session["user_id"] = abs(hash(entered_name)) % (10**8)
            return redirect(url_for("index"))
            
        elif action == "coinflip":
            try:
                amount = int(request.form.get("amount", 0))
                side = request.form.get("side") # RED or BLUE
            except ValueError:
                return redirect(url_for("index"))
                
            tokens, wagered = get_user(session["user_id"], session.get("username", "Oyuncu"))
            
            if amount <= 0 or amount > tokens:
                return render_template("index.html", error="Yetersiz bakiye!", tokens=tokens, wagered=wagered, username=session.get("username"))
                
            # Şans hesaplama (Kasa %51, Oyuncu %49)
            house_chance = 0.51
            winning_side = "BLUE" if random.random() < house_chance else side
            win = (side == winning_side)
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if win:
                payout = amount * 2
                new_tokens = tokens - amount + payout
                cursor.execute("UPDATE users SET tokens = ?, wagered = wagered + ? WHERE user_id = ?", (new_tokens, amount, session["user_id"]))
                result_msg = f"Tebrikler! Kazandın +{payout} Token (Gelen: {winning_side})"
            else:
                new_tokens = tokens - amount
                cursor.execute("UPDATE users SET tokens = ?, wagered = wagered + ? WHERE user_id = ?", (new_tokens, amount, session["user_id"]))
                result_msg = f"Kaybettin -{amount} Token (Gelen: {winning_side})"
                
            conn.commit()
            conn.close()
            
            tokens, wagered = get_user(session["user_id"], session.get("username"))
            return render_template("index.html", message=result_msg, tokens=tokens, wagered=wagered, username=session.get("username"))

    tokens, wagered = get_user(user_id, username)
    return render_template("index.html", tokens=tokens, wagered=wagered, username=session.get("username", ""))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)