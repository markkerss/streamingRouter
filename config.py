import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

ROUTER_PORT = int(os.getenv("ROUTER_PORT"))

# Helper function to get router address
def get_router_address():
    return ROUTER_PORT