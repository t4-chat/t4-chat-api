from typing import Any, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar, Union

from sqlalchemy import func
from sqlalchemy import select as sqlalchemy_select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select, and_, delete, select, update
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
                if len(join_item) == 2:
                    entity, condition = join_item
                    stmt = stmt.join(entity, condition)
                else:
                    stmt = stmt.join(join_item[0], join_item[1])
            else:
                stmt = stmt.join(join_item)
        return stmt

    async def get(
        self,
        joins: Optional[Sequence[JoinTarget]] = None,
        filter: Optional[ClauseElement] = None,
        includes: Optional[Sequence[Any]] = None,
        order_by: Optional[Union[Any, Sequence[Any]]] = None,
    ) -> Optional[T]:
        stmt = select(self.model)
        stmt = self._apply_joins(stmt, joins)

        if includes:
            for rel in includes:
                stmt = stmt.options(selectinload(rel))

        if filter is not None:
            stmt = stmt.where(filter)

        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                stmt = stmt.order_by(*order_by)
            else:
                stmt = stmt.order_by(order_by)

        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def select(
        self,
        *,
        columns: Optional[List[Any]] = None,
        joins: Optional[Sequence[Any]] = None,
        filter: Optional[ClauseElement] = None,
        includes: Optional[Sequence[Any]] = None,
        group_by: Optional[List[Any]] = None,
        order_by: Optional[Union[Any, Sequence[Any]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        as_dict: bool = False,
    ) -> Union[List[T], List[Dict[str, Any]]]:
        """
        Unified select method that handles both regular and aggregated queries.

        Args:
            columns: Optional list of columns to select. If None, selects the model.
            joins: Optional sequence of join targets
            filter: Optional filter condition
            includes: Optional sequence of relationships to include (eager loading)
            group_by: Optional list of columns/expressions to group by
            order_by: Optional ordering (single expression or sequence of expressions)
            limit: Optional limit for number of results
            offset: Optional offset for results
            as_dict: Whether to return results as dictionaries (True) or model instances (False)

        Returns:
            List of model instances or dictionaries depending on parameters
        """
        # If columns are specified, we're doing a custom select
        if columns:
            stmt = sqlalchemy_select(*columns)
            is_aggregation = True
        else:
            # Regular model select
            stmt = sqlalchemy_select(self.model)
            is_aggregation = False

        # Apply joins
        if joins:
            for join_item in joins:
                if isinstance(join_item, tuple) and len(join_item) == 2:
                    entity, condition = join_item
                    stmt = stmt.join(entity, condition)
                else:
                    stmt = stmt.join(join_item)

        # Apply includes (only for model selects)
        if includes and not is_aggregation:
            for rel in includes:
                stmt = stmt.options(selectinload(rel))

        # Apply filter condition
        if filter is not None:
            stmt = stmt.where(filter)

        # Apply group by (only for aggregation)
        if group_by:
            stmt = stmt.group_by(*group_by)

        # Apply ordering
        if order_by is not None:
            if isinstance(order_by, (list, tuple)):
                stmt = stmt.order_by(*order_by)
            else:
                stmt = stmt.order_by(order_by)

        # Apply limit and offset
        if limit is not None:
            stmt = stmt.limit(limit)

        if offset is not None:
            stmt = stmt.offset(offset)

        # Execute the query
        result = await self.session.execute(stmt)

        # Process results based on type
        if is_aggregation or as_dict:
            return [dict(row._mapping) for row in result.fetchall()]
        else:
            return result.scalars().all()

    async def get_total(
        self,
        columns_to_sum: List[Any],
        filter: Optional[ClauseElement] = None,
    ) -> Dict[str, Any]:
        """
        Calculate totals for specified columns.

        Args:
            columns_to_sum: List of columns to sum
            filter: Optional filter condition

        Returns:
            Dictionary with sum values for each column
        """
        select_items = []
        for column in columns_to_sum:
            if hasattr(column, "key"):
                select_items.append(func.sum(column).label(column.key))
            else:
                # Handle expressions that don't have a .key attribute
                select_items.append(func.sum(column))

        stmt = sqlalchemy_select(*select_items)

        if filter is not None:
            stmt = stmt.where(filter)

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if row:
            return dict(row._mapping)
        return {col.key if hasattr(col, "key") else f"sum_{i}": 0 for i, col in enumerate(columns_to_sum)}

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

    async def bulk_update(self, filter: ClauseElement, values: Dict[str, Any]) -> None:
        stmt = update(self.model).where(filter).values(**values)
        await self.session.execute(stmt)
        await self.session.flush()

    async def exists(self, filter: ClauseElement) -> bool:
        stmt = select(self.model).where(filter).exists()
        result = await self.session.execute(select(stmt))
        return result.scalar()
