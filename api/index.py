"""
Vercel Serverless Python Entrypoint.
Exposes the FastAPI application instance for Vercel's ASGI serverless runtime.
"""
import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
