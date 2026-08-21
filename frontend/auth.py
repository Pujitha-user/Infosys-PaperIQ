import json
import os
import bcrypt
from datetime import datetime
from pathlib import Path

# Database file paths
DB_DIR = Path(__file__).parent / "data"
USERS_DB = DB_DIR / "users.json"
HISTORY_DB = DB_DIR / "history.json"

# Create data directory if it doesn't exist
DB_DIR.mkdir(exist_ok=True)


def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hashed version"""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def load_users() -> dict:
    """Load users from database"""
    if USERS_DB.exists():
        with open(USERS_DB, 'r') as f:
            return json.load(f)
    return {}


def save_users(users: dict):
    """Save users to database"""
    with open(USERS_DB, 'w') as f:
        json.dump(users, f, indent=2)


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """
    Register a new user
    Returns: (success, message)
    """
    if not username or not email or not password:
        return False, "All fields are required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    
    users = load_users()
    
    if username in users:
        return False, "Username already exists"
    
    # Check if email already registered
    for user_data in users.values():
        if user_data['email'] == email:
            return False, "Email already registered"
    
    users[username] = {
        'email': email,
        'password': hash_password(password),
        'created_at': datetime.now().isoformat()
    }
    
    save_users(users)
    return True, "Registration successful!"


def login_user(username: str, password: str) -> tuple[bool, str]:
    """
    Login a user
    Returns: (success, message)
    """
    if not username or not password:
        return False, "Username and password required"
    
    users = load_users()
    
    if username not in users:
        return False, "Username not found"
    
    if not verify_password(password, users[username]['password']):
        return False, "Incorrect password"
    
    return True, "Login successful!"


def load_history() -> dict:
    """Load analysis history from database"""
    if HISTORY_DB.exists():
        with open(HISTORY_DB, 'r') as f:
            return json.load(f)
    return {}


def save_history(history: dict):
    """Save analysis history to database"""
    with open(HISTORY_DB, 'w') as f:
        json.dump(history, f, indent=2)


def add_to_history(username: str, text: str, results: dict) -> bool:
    """Add analysis result to user's history"""
    history = load_history()
    
    if username not in history:
        history[username] = []
    
    history_entry = {
        'timestamp': datetime.now().isoformat(),
        'text_preview': text[:100] + "..." if len(text) > 100 else text,
        'full_text': text,
        'results': results
    }
    
    history[username].append(history_entry)
    save_history(history)
    return True


def get_user_history(username: str) -> list:
    """Get analysis history for a user"""
    history = load_history()
    return history.get(username, [])


def delete_history_entry(username: str, index: int) -> bool:
    """Delete a specific history entry"""
    history = load_history()
    
    if username in history and 0 <= index < len(history[username]):
        del history[username][index]
        save_history(history)
        return True
    return False
