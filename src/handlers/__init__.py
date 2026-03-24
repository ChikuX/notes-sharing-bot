from .start import app as start_router
from .profile import app as profile_router
from .upload import app as upload_router
from .settings import app as settings_router
from .admin import app as admin_router

routers = [
    start_router,
    profile_router,
    upload_router,
    settings_router,
    admin_router,
]


def register_handlers(dp):
    for router in routers:
        dp.include_router(router)