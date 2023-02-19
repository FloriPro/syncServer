import os
import env
from supabase import create_client, Client

API_URL = os.environ['SUPA_API_URL']
API_KEY = os.environ['SUPA_API_KEY']

supabase: Client = create_client(API_URL, API_KEY)