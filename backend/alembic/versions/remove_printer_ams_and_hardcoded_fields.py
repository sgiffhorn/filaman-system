"""remove_printer_ams_and_hardcoded_fields

Remove printer_ams_units table, is_ams_slot/ams_unit_id from printer_slots,
and manufacturer/model/serial_number from printers.

Revision ID: remove_ams_fields
Revises: remove_expiration_date
Create Date: 2026-02-25 13:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'remove_ams_fields'
down_revision: Union[str, Sequence[str], None] = 'remove_expiration_date'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove AMS tables/columns and hardcoded printer fields."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    # On MySQL/MariaDB the FK on ams_unit_id blocks dropping its backing index
    # and column (error 1553/1025). The constraint was created unnamed in
    # 4b9f107a3faf_initial_tables, so the DB generated the name — look it up.
    # SQLite rebuilds the table in batch mode and doesn't need an explicit drop.
    if dialect in ('mysql', 'mariadb'):
        insp = inspect(bind)
        for fk in insp.get_foreign_keys('printer_slots'):
            if fk.get('constrained_columns') == ['ams_unit_id'] and fk.get('name'):
                op.drop_constraint(fk['name'], 'printer_slots', type_='foreignkey')
                break

    with op.batch_alter_table('printer_slots') as batch_op:
        batch_op.drop_constraint('uq_printer_slots_unique', type_='unique')
        batch_op.drop_index('ix_printer_slots_ams_unit_id')
        batch_op.drop_column('is_ams_slot')
        batch_op.drop_column('ams_unit_id')
        batch_op.create_unique_constraint('uq_printer_slots_unique', ['printer_id', 'slot_no'])

    # 2. Drop printer_ams_units table
    op.drop_table('printer_ams_units')

    # 3. Remove hardcoded fields from printers
    with op.batch_alter_table('printers') as batch_op:
        batch_op.drop_column('manufacturer')
        batch_op.drop_column('model')
        batch_op.drop_column('serial_number')


def downgrade() -> None:
    """Restore AMS tables/columns and hardcoded printer fields."""
    # 1. Restore columns on printers
    with op.batch_alter_table('printers') as batch_op:
        batch_op.add_column(sa.Column('manufacturer', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('model', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('serial_number', sa.String(100), nullable=True))

    # 2. Recreate printer_ams_units table
    op.create_table(
        'printer_ams_units',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('printer_id', sa.Integer(), nullable=False),
        sa.Column('ams_unit_no', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['printer_id'], ['printers.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('printer_id', 'ams_unit_no', name='uq_printer_ams_units_printer_unit'),
    )

    # 3. Restore AMS columns on printer_slots
    with op.batch_alter_table('printer_slots') as batch_op:
        batch_op.drop_constraint('uq_printer_slots_unique', type_='unique')
        batch_op.add_column(sa.Column('is_ams_slot', sa.Boolean(), nullable=False, server_default=sa.text('false')))
        batch_op.add_column(sa.Column('ams_unit_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_printer_slots_ams_unit_id_printer_ams_units',
            'printer_ams_units',
            ['ams_unit_id'],
            ['id'],
            ondelete='SET NULL',
        )
        batch_op.create_unique_constraint(
            'uq_printer_slots_unique',
            ['printer_id', 'is_ams_slot', 'ams_unit_id', 'slot_no'],
        )
        batch_op.create_index('ix_printer_slots_ams_unit_id', ['ams_unit_id'])
