import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import os

st.set_page_config(page_title="Private Messaging App - Database", layout="wide")
st.title("📱 Private Messaging System (Database Version)")

DB_PATH = os.path.join(st.secrets.get("db_path", "."), "messaging_app.db")

def init_database():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            recipient_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            read_status BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (recipient_id) REFERENCES users(id)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_users 
        ON messages (sender_id, recipient_id, timestamp)
    """)
    
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    password_hash = hash_password(password)
    cursor.execute(
        "SELECT id, username FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return {"id": result[0], "username": result[1]}
    return None

def get_all_users(exclude_user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_user_id:
        cursor.execute(
            "SELECT id, username FROM users WHERE id != ? ORDER BY username",
            (exclude_user_id,)
        )
    else:
        cursor.execute("SELECT id, username FROM users ORDER BY username")
    result = cursor.fetchall()
    conn.close()
    return result

def send_message(sender_id, recipient_id, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)",
        (sender_id, recipient_id, content)
    )
    conn.commit()
    conn.close()

def get_conversation(user1_id, user2_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.content, m.timestamp, u1.username as sender, m.sender_id
        FROM messages m
        JOIN users u1 ON m.sender_id = u1.id
        WHERE (m.sender_id = ? AND m.recipient_id = ?) 
           OR (m.sender_id = ? AND m.recipient_id = ?)
        ORDER BY m.timestamp ASC
    """, (user1_id, user2_id, user2_id, user1_id))
    result = cursor.fetchall()
    conn.close()
    return result

if not os.path.exists(DB_PATH):
    init_database()

if "user" not in st.session_state:
    st.session_state.user = None
if "selected_contact" not in st.session_state:
    st.session_state.selected_contact = None

# Authentication
if st.session_state.user is None:
    login_tab, register_tab = st.tabs(["Login", "Register"])
    with login_tab:
        st.subheader("👤 Login")
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Welcome back, {username}!")
                try:
                    st.experimental_rerun()
                except st.script_runner.RerunException:
                    return
            else:
                st.error("Invalid username or password")
    with register_tab:
        st.subheader("👤 Register")
        new_username = st.text_input("Choose Username", key="reg_username")
        new_password = st.text_input("Choose Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords don't match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            elif len(new_username) < 3:
                st.error("Username must be at least 3 characters")
            else:
                if create_user(new_username, new_password):
                    st.success("Account created successfully! Please login.")
                else:
                    st.error("Username already exists")
else:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.subheader("👥 Contacts")
        contacts = get_all_users(exclude_user_id=st.session_state.user["id"])
        for contact_id, contact_username in contacts:
            if st.button(f"💬 {contact_username}", key=f"contact_{contact_id}"):
                st.session_state.selected_contact = {"id": contact_id, "username": contact_username}
                try:
                    st.experimental_rerun()
                except st.script_runner.RerunException:
                    return
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.selected_contact = None
            try:
                st.experimental_rerun()
            except st.script_runner.RerunException:
                return
    with col2:
        if st.session_state.selected_contact:
            contact = st.session_state.selected_contact
            st.subheader(f"💬 Chat with {contact['username']}")
            conversation = get_conversation(st.session_state.user["id"], contact["id"])
            chat_container = st.container()
            with chat_container:
                for content, timestamp, sender_username, sender_id in conversation:
                    if sender_id == st.session_state.user["id"]:
                        with st.chat_message("user"):
                            st.write(content)
                            st.caption(f"Sent: {timestamp}")
                    else:
                        with st.chat_message("assistant"):
                            st.write(content)
                            st.caption(f"Received: {timestamp}")
            new_message = st.chat_input(f"Type a message to {contact['username']}...")
            if new_message:
                send_message(st.session_state.user["id"], contact["id"], new_message)
                try:
                    st.experimental_rerun()
                except st.script_runner.RerunException:
                    return
        else:
            st.info("👈 Select a contact to start chatting!")
            st.subheader("💬 Welcome to the Messaging System!")
            st.write("""
                - Private messaging between users  
                - Message persistence with SQLite database  
                - User authentication and registration  
                - Real-time message updates with refresh  
            """)
    
    if st.session_state.user and st.session_state.selected_contact:
        if st.button("🔄 Refresh Messages"):
            try:
                st.experimental_rerun()
            except st.script_runner.RerunException:
                return
