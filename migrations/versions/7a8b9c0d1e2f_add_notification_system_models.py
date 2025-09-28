"""Add notification system models

Revision ID: 7a8b9c0d1e2f
Revises: 5118c9068212
Create Date: 2025-01-23 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a8b9c0d1e2f'
down_revision = '5118c9068212'
branch_labels = None
depends_on = None


def upgrade():
    # Create notification table
    op.create_table('notification',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='system'),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('extra_data', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )

    # Create notification_settings table
    op.create_table('notification_settings',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('email_security', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_transaction', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_system', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('email_marketing', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('in_app_security', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('in_app_transaction', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('in_app_system', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('in_app_marketing', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('push_enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('push_security', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('push_transaction', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('push_system', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('quiet_hours_start', sa.Time(), nullable=True),
        sa.Column('quiet_hours_end', sa.Time(), nullable=True),
        sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], )
    )

    # Create indexes
    with op.batch_alter_table('notification') as batch_op:
        batch_op.create_index('idx_notification_user_category', ['user_id', 'category'])
        batch_op.create_index('idx_notification_user_read', ['user_id', 'is_read'])
        batch_op.create_index('idx_notification_created', ['created_at'])
        batch_op.create_index('idx_notification_priority', ['priority'])


def downgrade():
    # Drop indexes
    with op.batch_alter_table('notification') as batch_op:
        batch_op.drop_index('idx_notification_priority')
        batch_op.drop_index('idx_notification_created')
        batch_op.drop_index('idx_notification_user_read')
        batch_op.drop_index('idx_notification_user_category')

    # Drop tables
    op.drop_table('notification_settings')
    op.drop_table('notification')
