"""restricted app role for RLS enforcement

Revision ID: f36fa9caac33
Revises: 344f917eeec3
Create Date: 2026-07-08 21:56:58.866929

"""

import os
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f36fa9caac33"
down_revision: str | None = "344f917eeec3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The migration role (from DATABASE_URL, typically the DB's default superuser
# in local/dev setups) can create schema, but RLS policies have NO effect on
# a superuser or any role with BYPASSRLS - confirmed empirically while testing
# ADR 0003's isolation policies, which silently had zero effect under the
# superuser role despite being "enabled". Application services must connect
# as this separate, deliberately unprivileged role instead.
APP_ROLE = "asktherepo_app"
APP_ROLE_PASSWORD = os.environ.get("ASKTHEREPO_APP_DB_PASSWORD", "asktherepo_app_dev_only")


def upgrade() -> None:
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{APP_ROLE}') THEN
                CREATE ROLE {APP_ROLE} LOGIN PASSWORD '{APP_ROLE_PASSWORD}';
            END IF;
        END
        $$;
        """
    )
    # explicit, not just "new roles default to this" - the whole point is to
    # never again assume this without checking
    op.execute(f"ALTER ROLE {APP_ROLE} NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE}")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_ROLE}"
    )


def downgrade() -> None:
    op.execute(f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {APP_ROLE}")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM {APP_ROLE}")
    op.execute(f"DROP ROLE IF EXISTS {APP_ROLE}")
