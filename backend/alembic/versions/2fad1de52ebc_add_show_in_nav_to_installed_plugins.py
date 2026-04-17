"""add_show_in_nav_to_installed_plugins

Revision ID: 2fad1de52ebc
Revises: normalize_location_identifier
Create Date: 2026-03-13 23:21:28.705671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2fad1de52ebc'
down_revision: Union[str, Sequence[str], None] = 'normalize_location_identifier'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    # These indexes back FK constraints. On MySQL/MariaDB, dropping a FK-backing
    # index fails (error 1553) so rename in place. SQLite has no FK-index binding
    # and doesn't support ALTER TABLE ... RENAME INDEX, so drop+create instead.
    renames = [
        ('filament_printer_params', 'ix_filament_printer_params_filament', 'ix_filament_printer_params_filament_id', ['filament_id']),
        ('filament_printer_params', 'ix_filament_printer_params_printer', 'ix_filament_printer_params_printer_id', ['printer_id']),
        ('spool_printer_params', 'ix_spool_printer_params_spool', 'ix_spool_printer_params_spool_id', ['spool_id']),
        ('spool_printer_params', 'ix_spool_printer_params_printer', 'ix_spool_printer_params_printer_id', ['printer_id']),
    ]
    if dialect in ('mysql', 'mariadb'):
        for table, old, new, _cols in renames:
            op.execute(f'ALTER TABLE {table} RENAME INDEX {old} TO {new}')
    else:
        for table, old, new, cols in renames:
            op.drop_index(op.f(old), table_name=table)
            op.create_index(op.f(new), table, cols, unique=False)

    op.add_column('installed_plugins', sa.Column('show_in_nav', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    op.drop_column('installed_plugins', 'show_in_nav')

    renames = [
        ('filament_printer_params', 'ix_filament_printer_params_filament_id', 'ix_filament_printer_params_filament', ['filament_id']),
        ('filament_printer_params', 'ix_filament_printer_params_printer_id', 'ix_filament_printer_params_printer', ['printer_id']),
        ('spool_printer_params', 'ix_spool_printer_params_spool_id', 'ix_spool_printer_params_spool', ['spool_id']),
        ('spool_printer_params', 'ix_spool_printer_params_printer_id', 'ix_spool_printer_params_printer', ['printer_id']),
    ]
    if dialect in ('mysql', 'mariadb'):
        for table, old, new, _cols in renames:
            op.execute(f'ALTER TABLE {table} RENAME INDEX {old} TO {new}')
    else:
        for table, old, new, cols in renames:
            op.drop_index(op.f(old), table_name=table)
            op.create_index(op.f(new), table, cols, unique=False)
