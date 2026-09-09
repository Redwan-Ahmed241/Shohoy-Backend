from .repository import db as mem_db
from .connection import get_db, init_engine, Base
from .supabase_repository import supabase_repo
import config

# 'db' defaults to in-memory store, compatible with existing imports
db = mem_db
