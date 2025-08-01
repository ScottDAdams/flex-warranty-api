import os
from dotenv import load_dotenv
import logging

# Only load .env locally (not on Fly)
if not os.getenv("FLY_APP_NAME"):
    load_dotenv()

from app import create_app

logging.basicConfig(level=logging.DEBUG)

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 