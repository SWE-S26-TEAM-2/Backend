"""
Repository for Block database operations.

All raw queries for the blocks table live here.
"""

from sqlalchemy.orm import Session  # type: ignore

from app.models.block import Block  # type: ignore


class BlockRepository:

    @staticmethod
    def get_block(db: Session, blocker_id, blocked_id):
        """
        Find an existing block between two users.

        Args:
            db (Session): The database session.
            blocker_id: UUID of the user who blocked.
            blocked_id: UUID of the user who was blocked.

        Returns:
            Block or None: The block record if it exists.
        """
        return (
            db.query(Block)
            .filter(
                Block.blocker_id == blocker_id,
                Block.blocked_id == blocked_id,
            )
            .first()
        )

    @staticmethod
    def create_block(db: Session, blocker_id, blocked_id) -> Block:
        """
        Insert a new block record into the database.

        Args:
            db (Session): The database session.
            blocker_id: UUID of the user who is blocking.
            blocked_id: UUID of the user being blocked.

        Returns:
            Block: The newly created block record.
        """
        block = Block(
            blocker_id=blocker_id,
            blocked_id=blocked_id,
        )
        db.add(block)
        db.commit()
        db.refresh(block)
        return block

    @staticmethod
    def delete_block(db: Session, block: Block) -> None:
        """
        Delete an existing block record.

        Args:
            db (Session): The database session.
            block (Block): The block object to delete.
        """
        db.delete(block)
        db.commit()
