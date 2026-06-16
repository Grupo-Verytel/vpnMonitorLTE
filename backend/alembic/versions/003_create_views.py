"""Create SQL views for site channel queries.

Revision ID: 003
Revises: 001
Create Date: 2026-06-16
"""

from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL 8 supports CREATE OR REPLACE VIEW
    op.execute(
        """
        CREATE OR REPLACE VIEW v_latest_tunnel_state AS
        SELECT
            h.id AS snapshot_id,
            h.snapshot_time,
            d.tunnel_name,
            CASE
                WHEN SUM(CASE WHEN d.status = 'up' THEN 1 ELSE 0 END) > 0 THEN 'up'
                ELSE 'down'
            END AS status,
            SUM(d.incoming_bytes) AS incoming_bytes,
            SUM(d.outgoing_bytes) AS outgoing_bytes,
            SUM(COALESCE(d.incoming_bytes_delta, 0)) AS incoming_bytes_delta,
            SUM(COALESCE(d.outgoing_bytes_delta, 0)) AS outgoing_bytes_delta,
            MAX(d.remote_gateway) AS remote_gateway
        FROM vpn_snapshot_details d
        INNER JOIN vpn_snapshot_headers h ON d.snapshot_header_id = h.id
        WHERE h.id = (
            SELECT MAX(id) FROM vpn_snapshot_headers WHERE status = 'success'
        )
        GROUP BY h.id, h.snapshot_time, d.tunnel_name
        """
    )

    op.execute(
        """
        CREATE OR REPLACE VIEW v_sites_current AS
        SELECT
            c.tunnel_name,
            c.site_name,
            c.site_address,
            c.locality,
            c.project_code,
            c.contact_person,
            s.snapshot_time AS last_snapshot_time,
            s.status AS tunnel_status,
            s.incoming_bytes,
            s.outgoing_bytes,
            s.incoming_bytes_delta,
            s.outgoing_bytes_delta,
            s.remote_gateway
        FROM vpn_tunnels_catalog c
        LEFT JOIN v_latest_tunnel_state s ON c.tunnel_name = s.tunnel_name
        WHERE c.is_active = TRUE
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_sites_current")
    op.execute("DROP VIEW IF EXISTS v_latest_tunnel_state")
