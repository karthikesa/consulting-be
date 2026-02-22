"""Add vehicles and vehicle_images tables.

Revision ID: 002_vehicles
Revises: 001_initial
Create Date: 2025-02-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_vehicles"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("account_id", sa.Integer(), nullable=False),
        sa.Column("product", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("posting_date", sa.Date(), nullable=True),
        sa.Column("model_year", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicles_account_id"), "vehicles", ["account_id"], unique=False)
    op.create_index(op.f("ix_vehicles_product"), "vehicles", ["product"], unique=False)
    op.create_index(op.f("ix_vehicles_status"), "vehicles", ["status"], unique=False)

    op.create_table(
        "vehicle_images",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vehicle_id", sa.Integer(), nullable=False),
        sa.Column("image_path", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_vehicle_images_vehicle_id"), "vehicle_images", ["vehicle_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vehicle_images_vehicle_id"), table_name="vehicle_images")
    op.drop_table("vehicle_images")
    op.drop_index(op.f("ix_vehicles_status"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_product"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_account_id"), table_name="vehicles")
    op.drop_table("vehicles")
