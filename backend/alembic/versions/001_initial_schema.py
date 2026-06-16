"""Initial schema: snapshot headers, details, tunnel catalog.

Revision ID: 001
Revises:
Create Date: 2026-06-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vpn_snapshot_headers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("snapshot_time", sa.DateTime(), nullable=False),
        sa.Column("fortigate_serial", sa.String(length=50), nullable=True),
        sa.Column("fortigate_version", sa.String(length=20), nullable=True),
        sa.Column("total_tunnels", sa.Integer(), nullable=True),
        sa.Column("tunnels_up", sa.Integer(), nullable=True),
        sa.Column("tunnels_down", sa.Integer(), nullable=True),
        sa.Column("fetch_duration_ms", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="success"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vpn_snapshot_headers_snapshot_time",
        "vpn_snapshot_headers",
        ["snapshot_time"],
        unique=False,
    )
    op.create_index(
        "ix_vpn_snapshot_headers_snapshot_time_desc",
        "vpn_snapshot_headers",
        [sa.text("snapshot_time DESC")],
        unique=False,
    )

    op.create_table(
        "vpn_snapshot_details",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("snapshot_header_id", sa.BigInteger(), nullable=False),
        sa.Column("tunnel_name", sa.String(length=100), nullable=False),
        sa.Column("p2name", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=10), nullable=True),
        sa.Column("remote_gateway", sa.String(length=50), nullable=True),
        sa.Column("proxy_src", sa.String(length=255), nullable=True),
        sa.Column("proxy_dst", sa.String(length=255), nullable=True),
        sa.Column("incoming_bytes", sa.BigInteger(), nullable=True),
        sa.Column("outgoing_bytes", sa.BigInteger(), nullable=True),
        sa.Column("incoming_bytes_delta", sa.BigInteger(), nullable=True),
        sa.Column("outgoing_bytes_delta", sa.BigInteger(), nullable=True),
        sa.Column("creation_time", sa.BigInteger(), nullable=True),
        sa.Column("connection_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["snapshot_header_id"],
            ["vpn_snapshot_headers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vpn_snapshot_details_snapshot_header_id",
        "vpn_snapshot_details",
        ["snapshot_header_id"],
        unique=False,
    )
    op.create_index(
        "ix_vpn_snapshot_details_tunnel_name",
        "vpn_snapshot_details",
        ["tunnel_name"],
        unique=False,
    )
    op.create_index(
        "ix_vpn_snapshot_details_tunnel_header",
        "vpn_snapshot_details",
        ["tunnel_name", "snapshot_header_id"],
        unique=False,
    )

    op.create_table(
        "vpn_tunnels_catalog",
        sa.Column("tunnel_name", sa.String(length=100), nullable=False),
        sa.Column("site_name", sa.String(length=200), nullable=True),
        sa.Column("site_address", sa.String(length=300), nullable=True),
        sa.Column("locality", sa.String(length=100), nullable=True),
        sa.Column("project_code", sa.String(length=50), nullable=True),
        sa.Column("contact_person", sa.String(length=150), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("tunnel_name"),
    )


def downgrade() -> None:
    op.drop_table("vpn_tunnels_catalog")
    op.drop_index("ix_vpn_snapshot_details_tunnel_header", table_name="vpn_snapshot_details")
    op.drop_index("ix_vpn_snapshot_details_tunnel_name", table_name="vpn_snapshot_details")
    op.drop_index("ix_vpn_snapshot_details_snapshot_header_id", table_name="vpn_snapshot_details")
    op.drop_table("vpn_snapshot_details")
    op.drop_index("ix_vpn_snapshot_headers_snapshot_time_desc", table_name="vpn_snapshot_headers")
    op.drop_index("ix_vpn_snapshot_headers_snapshot_time", table_name="vpn_snapshot_headers")
    op.drop_table("vpn_snapshot_headers")
