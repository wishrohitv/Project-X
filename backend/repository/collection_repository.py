from database import SessionLocal
from models import CollectionData, Collections
from modules import datetime, delete, or_, sessionmaker, update
from utils import AppError, InternalServerError, ResourceNotFoundError, SuccessResponse


def _collections():
    pass


def _create_collection(
    name: str,
    session_user_id: int,
    description: str | None = None,
):
    session = SessionLocal()
    try:
        stmt = Collections(name=name, description=description, owner=session_user_id)
        session.add(stmt)
        session.commit()
        session.close()
    except AppError:
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while creating collections") from e


def _add_post_to_collection(collection_id: int, session_user_id: int, post_id: int):
    session = SessionLocal()
    try:
        collection = (
            session.query(Collections)
            .where(
                Collections.id == collection_id, Collections.owner == session_user_id
            )
            .first()
        )
        if not collection:
            raise ResourceNotFoundError("Collection not found")
        stmt = CollectionData(collection_id=collection_id, post_id=post_id)
        session.add(stmt)
        session.commit()
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while adding post to collection") from e
    finally:
        session.close()


def _remove_post_to_collection(collection_id: int, session_user_id: int, post_id: int):
    session = SessionLocal()
    try:
        collection = (
            session.query(Collections)
            .where(
                Collections.id == collection_id, Collections.owner == session_user_id
            )
            .first()
        )
        if not collection:
            raise ResourceNotFoundError("Collection not found or unauthorized")
        stmt = delete(CollectionData).filter_by(
            collection_id=collection_id, post_id=post_id
        )
        session.execute(stmt)
        session.commit()
    except AppError:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise InternalServerError("Error while removing post from collection") from e
    finally:
        session.close()


def _delete_collection(collection_id: int, session_user_id: int):
    session = SessionLocal()
    try:
        collection = (
            session.query(Collections)
            .where(
                Collections.id == collection_id, Collections.owner == session_user_id
            )
            .first()
        )
        if not collection:
            raise ResourceNotFoundError("Collection not found or unauthorized")
        stmt = delete(CollectionData).filter_by(collection_id=collection_id)
        stmt1 = delete(Collections).filter_by(id=collection_id)
        session.execute(stmt)
        session.execute(stmt1)
        session.commit()
        session.close()
    except Exception as e:
        session.rollback()
        raise InternalServerError(f"Error while deleting collection") from e
