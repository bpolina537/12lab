"""Initial schema for webinar platform

Создание основных таблиц с проверкой на существование (для безопасного повторного запуска)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()

    # ========================================
    # Таблица Rooms
    # ========================================
    if not bind.dialect.has_table(bind, "rooms"):
        op.create_table(
            'rooms',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('speaker', sa.String(length=100), nullable=False),
            sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

            sa.PrimaryKeyConstraint('id'),
            sa.Index('ix_rooms_status', 'status'),
            sa.Index('ix_rooms_created_at', 'created_at'),
        )

    # ========================================
    # Таблица Recordings
    # ========================================
    if not bind.dialect.has_table(bind, "recordings"):
        op.create_table(
            'recordings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('video_url', sa.String(), nullable=False),
            sa.Column('duration', sa.Integer(), nullable=False),
            sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
            sa.Index('ix_recordings_room_id', 'room_id'),
        )

    # ========================================
    # Таблица Chat Messages
    # ========================================
    if not bind.dialect.has_table(bind, "chat_messages"):
        op.create_table(
            'chat_messages',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),

            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
            sa.Index('ix_chat_messages_room_id', 'room_id'),
            sa.Index('ix_chat_messages_timestamp', 'timestamp'),
        )

    # ========================================
    # Таблица Polls
    # ========================================
    if not bind.dialect.has_table(bind, "polls"):
        op.create_table(
            'polls',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('question', sa.String(length=500), nullable=False),
            sa.Column('options_json', sa.JSON(), nullable=False),

            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint(
                'poll_id',
                'username',
                name='uq_poll_user_vote'
            ),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
            sa.Index('ix_polls_room_id', 'room_id'),
        )

    # ========================================
    # Таблица Poll Answers
    # ========================================
    if not bind.dialect.has_table(bind, "poll_answers"):
        op.create_table(
            'poll_answers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('poll_id', sa.Integer(), nullable=False),
            sa.Column('room_id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=100), nullable=False),
            sa.Column('selected_option', sa.String(length=200), nullable=False),

            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['poll_id'], ['polls.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['room_id'], ['rooms.id'], ondelete='CASCADE'),
            sa.Index('ix_poll_answers_poll_id', 'poll_id'),
            sa.Index('ix_poll_answers_room_id', 'room_id'),
            sa.Index('ix_poll_answers_username', 'username'),
        )


def downgrade():
    # Удаляем в обратном порядке
    op.drop_table('poll_answers')
    op.drop_table('polls')
    op.drop_table('chat_messages')
    op.drop_table('recordings')
    op.drop_table('rooms')