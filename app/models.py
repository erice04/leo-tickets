from datetime import datetime, timezone

from app.auth.permissions import Role
from app.extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    roles = db.relationship(
        "RoleAssignment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def role_names(self) -> set[str]:
        return {assignment.role for assignment in self.roles}

    def has_role(self, role: Role | str) -> bool:
        name = role.value if isinstance(role, Role) else role
        return name in self.role_names()

    def has_any_role(self, roles: set[Role]) -> bool:
        names = {r.value for r in roles}
        return bool(names & self.role_names())

    def grant_role(self, role: Role) -> None:
        if not self.has_role(role):
            self.roles.append(RoleAssignment(role=role.value))

    def revoke_role(self, role: Role) -> None:
        self.roles = [r for r in self.roles if r.role != role.value]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "is_active": self.is_active,
            "roles": sorted(self.role_names()),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RoleAssignment(db.Model):
    __tablename__ = "role_assignments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(32), nullable=False)

    user = db.relationship("User", back_populates="roles")

    __table_args__ = (db.UniqueConstraint("user_id", "role", name="uq_user_role"),)


class EventSettings(db.Model):
    """Single-row configuration for the active event."""

    __tablename__ = "event_settings"

    DEFAULT_CONTACT_EMAIL = "leosocialchairs@gmail.com"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, default="Event")
    image_visible = db.Column(db.Boolean, nullable=False, default=True)
    watermark_image = db.Column(db.LargeBinary, nullable=True)
    watermark_content_type = db.Column(db.String(64), nullable=True)
    contact_email = db.Column(
        db.String(255), nullable=False, default=DEFAULT_CONTACT_EMAIL
    )
    default_theme = db.Column(db.String(8), nullable=False, default="light")
    postcard_enabled = db.Column(db.Boolean, nullable=False, default=False)
    postcard_stamp_default = db.Column(db.Boolean, nullable=False, default=False)
    postcard_stamp_orientation = db.Column(db.String(16), nullable=False, default="vertical")
    watermark_preset = db.Column(db.String(16), nullable=False, default="none")
    postcard_stamp_preset = db.Column(db.String(24), nullable=False, default="sterling")
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    @classmethod
    def get(cls):
        settings = db.session.get(cls, 1)
        if settings is None:
            settings = cls(
                id=1,
                title="Event",
                image_visible=True,
                contact_email=cls.DEFAULT_CONTACT_EMAIL,
                default_theme="light",
                postcard_enabled=False,
                postcard_stamp_default=False,
                postcard_stamp_orientation="vertical",
                watermark_preset="none",
                postcard_stamp_preset="sterling",
            )
            db.session.add(settings)
            db.session.commit()
        return settings

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "image_visible": self.image_visible,
            "has_custom_watermark": self.watermark_image is not None,
            "watermark_preset": self.watermark_preset,
            "contact_email": self.contact_email,
            "default_theme": self.default_theme,
            "postcard_enabled": self.postcard_enabled,
            "postcard_stamp_default": self.postcard_stamp_default,
            "postcard_stamp_orientation": self.postcard_stamp_orientation,
            "postcard_stamp_preset": self.postcard_stamp_preset,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def uses_custom_watermark(self) -> bool:
        return self.watermark_image is not None


class AllowedEmail(db.Model):
    __tablename__ = "allowed_emails"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class BlacklistedEmail(db.Model):
    __tablename__ = "blacklisted_emails"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class YaleStudent(db.Model):
    __tablename__ = "yale_students"

    email = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.String(255))
    image_url = db.Column(db.Text)
    year = db.Column(db.String(10))
    netid = db.Column(db.String(50))
    birthday = db.Column(db.String(50))
    major = db.Column(db.String(255))
    address = db.Column(db.Text)
    updated_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow
    )

    def to_public_dict(self, include_image: bool = True) -> dict:
        image_url = self.image_url if include_image else ""
        if image_url in (None, "None"):
            image_url = ""
        return {
            "email": self.email,
            "name": self.name or "N/A",
            "image_url": image_url or "",
            "year": self.year,
            "netid": self.netid,
        }


class ScanLog(db.Model):
    __tablename__ = "scan_logs"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, index=True)
    scanned_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )
    scanned_by = db.Column(db.String(255))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "scanned_at": self.scanned_at.isoformat() if self.scanned_at else None,
            "scanned_by": self.scanned_by,
        }
