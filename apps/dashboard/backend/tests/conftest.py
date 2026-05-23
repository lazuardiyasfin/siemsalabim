import sys
import os
from pathlib import Path
import importlib.util
import bcrypt

# Set mock environment variables before executing modules
MOCK_PASSWORD = "admin123"
MOCK_HASH = bcrypt.hashpw(MOCK_PASSWORD.encode(), bcrypt.gensalt()).decode()

os.environ["DASHBOARD_USER"] = "admin"
os.environ["DASHBOARD_PASSWORD_HASH"] = MOCK_HASH
os.environ["DASHBOARD_JWT_SECRET_KEY"] = "super-secret-key-for-testing-12345"

# Add src directory to path so dashboard-backend can be imported
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Create an alias for the dashboard-backend module (directory has hyphen, import expects underscore)

dashboard_backend_path = src_path / "dashboard-backend"
if dashboard_backend_path.exists():
    spec = importlib.util.spec_from_file_location(
        "dashboard_backend", dashboard_backend_path / "__init__.py"
    )
    if spec and spec.loader:
        dashboard_backend = importlib.util.module_from_spec(spec)
        sys.modules["dashboard_backend"] = dashboard_backend
        spec.loader.exec_module(dashboard_backend)
