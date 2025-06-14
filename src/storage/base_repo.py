from typing import Any, Awaitable, Callable, Generic, List, Optional, Sequence, Tuple, Type, TypeVar, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select, delete, select
from sqlalchemy.sql.elements import ClauseElement

T = TypeVar("T")
JoinTarget = Union[Any, Tuple[Any, Any]]


class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    def _apply_joins(self, stmt: Select, joins: Optional[Sequence[JoinTarget]]) -> Select:
        if not joins:
            return stmt

        for join_item in joins:
            if isinstance(join_item, tuple):
                stmt = stmt.join(join_item[0], join_item[1])
            else:
                stmt = stmt.join(join_item)
        return stmt

    async def get(
        self,
        joins: Optional[Sequence[JoinTarget]] = None,
        filter: Optional[ClauseElement] = None,
        includes: Optional[Sequence[Any]] = None,
    ) -> Optional[T]:
        stmt = select(self.model)
        stmt = self._apply_joins(stmt, joins)

        if includes:
            for rel in includes:
                stmt = stmt.options(selectinload(rel))

        if filter is not None:
            stmt = stmt.where(filter)

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_first(
        self,
        joins: Optional[Sequence[Any]] = None,
        filter: Optional[ClauseElement] = None,
        includes: Optional[Sequence[Any]] = None,
        order_by: Optional[Any] = None,
    ) -> Optional[T]:
        stmt = select(self.model)
        stmt = self._apply_joins(stmt, joins)

        if includes:
            for rel in includes:
                stmt = stmt.options(selectinload(rel))

        if filter is not None:
            stmt = stmt.where(filter)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        joins: Optional[Sequence[Any]] = None,
        filter: Optional[ClauseElement] = None,
        includes: Optional[Sequence[Any]] = None,
        order_by: Optional[Any] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        stmt = select(self.model)
        stmt = self._apply_joins(stmt, joins)

        if includes:
            for rel in includes:
                stmt = stmt.options(selectinload(rel))

        if filter is not None:
            stmt = stmt.where(filter)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: T) -> T:
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: T) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def delete_by_filter(self, filter: ClauseElement) -> None:
        stmt = delete(self.model).where(filter)
        await self.session.execute(stmt)
        await self.session.flush()

    async def exists(self, filter: ClauseElement) -> bool:
        stmt = select(self.model).where(filter).exists()
        result = await self.session.execute(select(stmt))
        return result.scalar()
