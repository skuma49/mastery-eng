#!/usr/bin/env python3
"""
Simple test script to check if all imports work
"""

print("Testing imports...")

try:
    from flask import Flask
    print("✅ Flask imported successfully")
except ImportError as e:
    print(f"❌ Flask import failed: {e}")

try:
    from flask_wtf.csrf import CSRFProtect
    print("✅ Flask-WTF imported successfully")
except ImportError as e:
    print(f"❌ Flask-WTF import failed: {e}")

try:
    from flask_limiter import Limiter
    print("✅ Flask-Limiter imported successfully")
except ImportError as e:
    print(f"❌ Flask-Limiter import failed: {e}")

try:
    import bleach
    print("✅ Bleach imported successfully")
except ImportError as e:
    print(f"❌ Bleach import failed: {e}")

try:
    from models import db
    print("✅ Models imported successfully")
except ImportError as e:
    print(f"❌ Models import failed: {e}")

try:
    from forms import VocabularyForm
    print("✅ Forms imported successfully")
except ImportError as e:
    print(f"❌ Forms import failed: {e}")

try:
    from config import DevelopmentConfig
    print("✅ Config imported successfully")
except ImportError as e:
    print(f"❌ Config import failed: {e}")

print("\nTesting app creation...")
try:
    from app import create_app
    app = create_app()
    print("✅ App created successfully")
    print(f"✅ App name: {app.name}")
    print(f"✅ Debug mode: {app.debug}")
except Exception as e:
    print(f"❌ App creation failed: {e}")

print("\nAll tests completed!")
