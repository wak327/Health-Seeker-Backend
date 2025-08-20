from app.core import security
from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.models import Base
from app.models.user import User, UserRole


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _create_default_superadmin()


def _create_default_superadmin() -> None:
    settings = get_settings()
    if not settings.superadmin_email or not settings.superadmin_password:
        return

    with SessionLocal() as session:
        existing = (
            session.query(User)
            .filter(User.email == settings.superadmin_email)
            .one_or_none()
        )
        if existing:
            return

        superadmin = User(
            email=settings.superadmin_email,
            full_name=settings.superadmin_full_name,
            role=UserRole.SUPERADMIN,
            hashed_password=security.hash_password(settings.superadmin_password),
            is_active=True,
        )
        session.add(superadmin)
        session.commit()
