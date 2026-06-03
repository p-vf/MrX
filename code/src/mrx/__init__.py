from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from .communication.server import main as server_main
from .communication.client import main as client_main
from .database.create_user_db import main as create_db_main
from .database.user_db_test import main as test_db_main
from .gui.client_stub import main as gui_main