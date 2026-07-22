#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
import os

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")