import os
from dotenv import load_dotenv

load_dotenv()

ROUTER_PORT = os.getenv("ROUTER_PORT")
ROUTER_IP = os.getenv("ROUTER_IP")
