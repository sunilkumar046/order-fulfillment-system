from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.role import Role


DEFAULT_ROLES = [
    "Admin",
    "Warehouse Manager",
    "Fulfillment Agent",
    "Customer",
]


def seed_roles() -> None:
    db = SessionLocal()

    try:
        for role_name in DEFAULT_ROLES:
            existing_role = db.scalar(
                select(Role).where(Role.name == role_name)
            )

            if existing_role:
                print(f"Role already exists: {role_name}")
                continue

            role = Role(name=role_name)
            db.add(role)

            print(f"Created role: {role_name}")

        db.commit()
        print("Role seeding completed successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()