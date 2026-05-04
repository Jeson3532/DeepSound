from sqlalchemy import select, exists, insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.database.pg.tables import Users, AnalysisHistory
from sqlalchemy.exc import IntegrityError
from src.services.methods import get_hash_password

from src.schemas.base.auth import UserRegister
import logging
import src.exceptions as exc

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class DatabaseService:

    def __init__(self, session: AsyncSession):
        self._session = session
        self.users = UsersService(session)
        self.history = HistoryService(session)
        # self.Profiles = Profiles(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class UsersService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add_user(self, user: UserRegister) -> Users | None:
        try:
            user_dict = user.model_dump(exclude={"password", "repeat_password"})
            new_user = Users(**user_dict, hash_password=get_hash_password(user.password))
            self._session.add(new_user)
            await self._session.flush()
            await self._session.refresh(new_user)
            return new_user
        except IntegrityError as e:
            logger.warning(f"Попытка создать дубликат в {self.__class__.__name__}. Traceback: {e}")
            await self._session.rollback()
            raise exc.UserAlreadyExists("Данный пользователь уже существует") from e
        except Exception as e:
            logger.error(f"Общая ошибка в {self.__class__.__name__}. Traceback: {e}")
            await self._session.rollback()
            raise


class HistoryService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save_analysis(self, username: str, data: dict) -> AnalysisHistory:
        record = AnalysisHistory(username=username, **data)
        self._session.add(record)
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_user_history(self, username: str) -> list[AnalysisHistory]:
        result = await self._session.execute(
            select(AnalysisHistory)
            .where(AnalysisHistory.username == username)
            .order_by(AnalysisHistory.created_at.desc())
        )
        return result.scalars().all()
