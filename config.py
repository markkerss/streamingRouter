import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

ROUTER_PORT = os.getenv("ROUTER_PORT")
ROUTER_IP = os.getenv("ROUTER_IP")