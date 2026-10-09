"""
add returns and order agent assignment

Revision ID: e0b3b4a2216d
Revises: 984f8c435e4b
Create Date: 2026-09-30 10:40:26.752942
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e0b3b4a2216d"
down_revision: Union[str, Sequence[str], None] = "984f8c435e4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # ---------------------------------------------------------
    # Return Requests
    # ---------------------------------------------------------
    op.create_table(
        "return_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["approved_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_return_requests_customer_id"),
        "return_requests",
        ["customer_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_return_requests_id"),
        "return_requests",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_return_requests_order_id"),
        "return_requests",
        ["order_id"],
        unique=True,
    )

    op.create_index(
        op.f("ix_return_requests_status"),
        "return_requests",
        ["status"],
        unique=False,
    )

    # ---------------------------------------------------------
    # Return Items
    # ---------------------------------------------------------
    op.create_table(
        "return_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("return_request_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("condition", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.ForeignKeyConstraint(
            ["return_request_id"],
            ["return_requests.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_return_items_id"),
        "return_items",
        ["id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_return_items_product_id"),
        "return_items",
        ["product_id"],
        unique=False,
    )

    op.create_index(
        op.f("ix_return_items_return_request_id"),
        "return_items",
        ["return_request_id"],
        unique=False,
    )

    # ---------------------------------------------------------
    # Order Agent Assignment
    # ---------------------------------------------------------
    op.add_column(
        "orders",
        sa.Column(
            "assigned_agent_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_orders_assigned_agent_id"),
        "orders",
        ["assigned_agent_id"],
        unique=False,
    )

    op.create_foreign_key(
        "fk_orders_assigned_agent_id_users",
        "orders",
        "users",
        ["assigned_agent_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Remove order agent assignment
    op.drop_constraint(
        "fk_orders_assigned_agent_id_users",
        "orders",
        type_="foreignkey",
    )

    op.drop_index(
        op.f("ix_orders_assigned_agent_id"),
        table_name="orders",
    )

    op.drop_column(
        "orders",
        "assigned_agent_id",
    )

    # Remove return items
    op.drop_index(
        op.f("ix_return_items_return_request_id"),
        table_name="return_items",
    )

    op.drop_index(
        op.f("ix_return_items_product_id"),
        table_name="return_items",
    )

    op.drop_index(
        op.f("ix_return_items_id"),
        table_name="return_items",
    )

    op.drop_table("return_items")

    # Remove return requests
    op.drop_index(
        op.f("ix_return_requests_status"),
        table_name="return_requests",
    )

    op.drop_index(
        op.f("ix_return_requests_order_id"),
        table_name="return_requests",
    )

    op.drop_index(
        op.f("ix_return_requests_id"),
        table_name="return_requests",
    )

    op.drop_index(
        op.f("ix_return_requests_customer_id"),
        table_name="return_requests",
    )

    op.drop_table("return_requests")