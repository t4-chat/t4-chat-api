"""
Reusable filtering system for API endpoints.

Usage:
1. In your endpoint, extract query parameters:
   query_params = dict(request.query_params)
   
2. Parse filters:
   filter_specs = FiltersParser.parse_filters(query_params)
   
3. Build SQLAlchemy conditions:
   custom_filter = SQLAlchemyFilterBuilder.build_filters(YourModel, filter_specs)
   
4. Apply to your query:
   results = await your_repo.select(filter=custom_filter)

Supported filter formats:
- filter[field]=value          -> field contains value (for arrays) or equals value
- filter[field]=val1,val2      -> field contains any of val1 or val2
- filter[field]=val1&filter[field]=val2 -> field contains val1 OR val2

Examples:
- filter[modalities]=text      -> models with 'text' in modalities array
- filter[modalities]=text,image -> models with 'text' OR 'image' in modalities
- filter[tags]=ai&filter[tags]=llm -> models with 'ai' OR 'llm' in tags
"""

from typing import Any, Dict, List, Optional, Type, Union

from pydantic import BaseModel
from sqlalchemy import Column, and_, or_
from sqlalchemy.sql import ColumnElement


class FilterValue(BaseModel):
    """Represents a filter value with its operation type"""
    value: Union[str, List[str], int, float, bool]
    operation: str = "eq"  # eq, in, contains, like, gt, gte, lt, lte


class FilterSpec(BaseModel):
    """Specification for a single filter"""
    field: str
    values: List[FilterValue]
    operator: str = "or"  # and, or - how to combine multiple values


class FiltersParser:
    """Parser for handling filter query parameters in the format filter[field]=value"""

    @staticmethod
    def parse_filters(query_params: Dict[str, Any]) -> List[FilterSpec]:
        """
        Parse filter parameters from query params
        
        Examples:
        - filter[modalities]=text -> FilterSpec(field="modalities", values=[FilterValue(value="text", operation="contains")])
        - filter[modalities]=text,image -> FilterSpec(field="modalities", values=[FilterValue(value=["text", "image"], operation="in")])
        - filter[tags]=tag1&filter[tags]=tag2 -> FilterSpec(field="tags", values=[FilterValue(value="tag1"), FilterValue(value="tag2")])
        """
        filters = {}

        for key, value in query_params.items():
            if not key.startswith("filter[") or not key.endswith("]"):
                continue

            field_name = key[7:-1]  # Remove "filter[" and "]"

            if field_name not in filters:
                filters[field_name] = []

            # Handle comma-separated values for array fields
            if isinstance(value, str) and "," in value:
                filter_values = [FilterValue(value=v.strip(), operation="contains") for v in value.split(",")]
            elif isinstance(value, list):
                filter_values = [FilterValue(value=v, operation="contains") for v in value]
            else:
                filter_values = [FilterValue(value=value, operation="contains")]

            filters[field_name].extend(filter_values)

        return [FilterSpec(field=field, values=values) for field, values in filters.items()]


class SQLAlchemyFilterBuilder:
    """Builds SQLAlchemy filter conditions from FilterSpec objects"""

    @staticmethod
    def build_filters(model_class: Type, filter_specs: List[FilterSpec]) -> Optional[ColumnElement]:
        """
        Build SQLAlchemy filter conditions from filter specifications
        
        Args:
            model_class: The SQLAlchemy model class
            filter_specs: List of filter specifications
            
        Returns:
            SQLAlchemy filter condition or None if no filters
        """
        if not filter_specs:
            return None

        conditions = []

        for filter_spec in filter_specs:
            field_condition = SQLAlchemyFilterBuilder._build_field_condition(
                model_class, filter_spec
            )
            if field_condition is not None:
                conditions.append(field_condition)

        if not conditions:
            return None

        # Combine all field conditions with AND
        return and_(*conditions)

    @staticmethod
    def _build_field_condition(model_class: Type, filter_spec: FilterSpec) -> Optional[ColumnElement]:
        """Build condition for a single field"""
        if not hasattr(model_class, filter_spec.field):
            return None

        column = getattr(model_class, filter_spec.field)
        value_conditions = []

        for filter_value in filter_spec.values:
            condition = SQLAlchemyFilterBuilder._build_value_condition(
                column, filter_value
            )
            if condition is not None:
                value_conditions.append(condition)

        if not value_conditions:
            return None

        # Combine value conditions based on operator (default OR)
        if filter_spec.operator == "and":
            return and_(*value_conditions)
        else:
            return or_(*value_conditions)

    @staticmethod
    def _build_value_condition(column: Column, filter_value: FilterValue) -> Optional[ColumnElement]:
        """Build condition for a single value"""
        operation = filter_value.operation
        value = filter_value.value

        if operation == "eq":
            return column == value
        elif operation == "in":
            if isinstance(value, list):
                return column.in_(value)
            else:
                return column == value
        elif operation == "contains":
            # For array columns, check if array contains the value
            if hasattr(column.type, 'item_type'):  # Array column
                if isinstance(value, list):
                    # Check if array contains any of the values
                    return or_(*[column.any(v) for v in value])
                else:
                    return column.any(value)
            else:
                # For string columns, use LIKE
                return column.like(f"%{value}%")
        elif operation == "like":
            return column.like(f"%{value}%")
        elif operation == "gt":
            return column > value
        elif operation == "gte":
            return column >= value
        elif operation == "lt":
            return column < value
        elif operation == "lte":
            return column <= value

        return None
