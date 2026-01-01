"""
SQL Mixin for Pydantic Models

Adds SQL generation capabilities to Pydantic models:
- CREATE TABLE statements from field definitions
- INSERT/SELECT/UPDATE statement generation
- SQLite and PostgreSQL dialect support
- Automatic JSON serialization for nested models
"""

import json
from datetime import datetime
from typing import Any, Optional, get_args, get_origin

from pydantic import BaseModel


class SQLMixin:
    """
    Mixin that adds SQL generation to Pydantic models.

    Usage:
        class MyModel(BaseModel, SQLMixin):
            id: str
            name: str
            tags: list[str]

        # Generate SQL
        create_sql = MyModel.create_table_sql(dialect="postgresql")
        insert_sql, params = MyModel.insert_sql()

        # Use with data
        obj = MyModel(id="1", name="Test", tags=["a", "b"])
        db_dict = obj.to_db_dict()
    """

    @classmethod
    def _get_table_name(cls) -> str:
        """Get table name from class config or class name"""
        if hasattr(cls, "model_config") and "table_name" in cls.model_config:
            return cls.model_config["table_name"]
        # Convert CamelCase to snake_case and pluralize
        name = cls.__name__
        # Simple snake_case conversion
        import re

        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
        # Simple pluralization
        if not snake.endswith("s"):
            snake += "s"
        return snake

    @classmethod
    def _python_type_to_sql(cls, python_type: Any, dialect: str = "postgresql") -> str:
        """
        Map Python type annotation to SQL type.

        Args:
            python_type: Python type annotation
            dialect: "postgresql" or "sqlite"

        Returns:
            SQL type string
        """
        # Handle Optional[T]
        origin = get_origin(python_type)
        if origin is type(None) or (hasattr(python_type, "__args__") and type(None) in python_type.__args__):
            # Extract the non-None type
            args = get_args(python_type)
            if args:
                python_type = args[0] if args[0] is not type(None) else args[1]
                origin = get_origin(python_type)

        # Handle list[T]
        if origin is list:
            if dialect == "postgresql":
                # PostgreSQL supports ARRAY types
                inner_type = get_args(python_type)[0] if get_args(python_type) else str
                inner_sql = cls._python_type_to_sql(inner_type, dialect)
                return f"{inner_sql}[]"
            else:
                # SQLite uses JSON for arrays
                return "TEXT"  # Will store as JSON

        # Handle dict
        if origin is dict or python_type is dict:
            return "JSONB" if dialect == "postgresql" else "TEXT"

        # Handle Pydantic models (nested)
        if isinstance(python_type, type) and issubclass(python_type, BaseModel):
            return "JSONB" if dialect == "postgresql" else "TEXT"

        # Basic types
        type_map = {
            str: "TEXT",
            int: "INTEGER",
            float: "DOUBLE PRECISION" if dialect == "postgresql" else "REAL",
            bool: "BOOLEAN",
            datetime: "TIMESTAMP WITH TIME ZONE" if dialect == "postgresql" else "TEXT",
        }

        return type_map.get(python_type, "TEXT")

    @classmethod
    def create_table_sql(cls, dialect: str = "postgresql", if_not_exists: bool = True) -> str:
        """
        Generate CREATE TABLE statement from Pydantic model.

        Args:
            dialect: "postgresql" or "sqlite"
            if_not_exists: Add IF NOT EXISTS clause

        Returns:
            CREATE TABLE SQL statement
        """
        table_name = cls._get_table_name()
        lines = []

        # Start CREATE TABLE
        if_not_exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        lines.append(f"CREATE TABLE {if_not_exists_clause}{table_name} (")

        # Add columns
        columns = []
        for field_name, field_info in cls.model_fields.items():
            sql_type = cls._python_type_to_sql(field_info.annotation, dialect)

            # Check if nullable
            is_optional = get_origin(field_info.annotation) is type(None) or (hasattr(field_info.annotation, "__args__") and type(None) in field_info.annotation.__args__)
            null_clause = "" if is_optional else " NOT NULL"

            # Check for primary key (simple heuristic: field named 'id')
            pk_clause = " PRIMARY KEY" if field_name == "id" else ""

            columns.append(f"    {field_name} {sql_type}{null_clause}{pk_clause}")

        lines.append(",\n".join(columns))
        lines.append(");")

        return "\n".join(lines)

    @classmethod
    def insert_sql(cls, dialect: str = "postgresql") -> tuple[str, list[str]]:
        """
        Generate INSERT statement.

        Args:
            dialect: "postgresql" or "sqlite"

        Returns:
            Tuple of (SQL statement, list of parameter names)
        """
        table_name = cls._get_table_name()
        field_names = list(cls.model_fields.keys())

        # Generate placeholders
        if dialect == "postgresql":
            placeholders = [f"${i+1}" for i in range(len(field_names))]
        else:  # sqlite
            placeholders = ["?" for _ in field_names]

        columns = ", ".join(field_names)
        values = ", ".join(placeholders)

        sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"

        return sql, field_names

    @classmethod
    def select_sql(cls, where: Optional[str] = None, columns: Optional[list[str]] = None) -> str:
        """
        Generate SELECT statement.

        Args:
            where: Optional WHERE clause (without WHERE keyword)
            columns: Optional list of columns to select (default: all)

        Returns:
            SELECT SQL statement
        """
        table_name = cls._get_table_name()

        if columns:
            column_list = ", ".join(columns)
        else:
            column_list = "*"

        sql = f"SELECT {column_list} FROM {table_name}"

        if where:
            sql += f" WHERE {where}"

        return sql

    @classmethod
    def update_sql(cls, where: str, dialect: str = "postgresql", fields: Optional[list[str]] = None) -> tuple[str, list[str]]:
        """
        Generate UPDATE statement.

        Args:
            where: WHERE clause (without WHERE keyword)
            dialect: "postgresql" or "sqlite"
            fields: Optional list of fields to update (default: all except id)

        Returns:
            Tuple of (SQL statement, list of parameter names)
        """
        table_name = cls._get_table_name()

        # Default: update all fields except id
        if fields is None:
            fields = [name for name in cls.model_fields.keys() if name != "id"]

        # Generate SET clause
        if dialect == "postgresql":
            set_clauses = [f"{field} = ${i+1}" for i, field in enumerate(fields)]
        else:  # sqlite
            set_clauses = [f"{field} = ?" for field in fields]

        set_clause = ", ".join(set_clauses)

        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where}"

        return sql, fields

    def to_db_dict(self, dialect: str = "postgresql") -> dict[str, Any]:
        """
        Convert model to dictionary suitable for database insertion.

        Handles:
        - JSON serialization of lists, dicts, and nested models
        - Datetime conversion

        Args:
            dialect: "postgresql" or "sqlite"

        Returns:
            Dictionary with database-ready values
        """
        # Use Pydantic's model_dump for JSON serialization
        data = self.model_dump(mode="json")

        # For SQLite, convert lists/dicts to JSON strings
        if dialect == "sqlite":
            for field_name, field_info in self.model_fields.items():
                value = data.get(field_name)
                if value is not None:
                    origin = get_origin(field_info.annotation)

                    # Convert lists and dicts to JSON strings
                    if origin is list or origin is dict:
                        data[field_name] = json.dumps(value)
                    # Convert nested Pydantic models to JSON strings
                    elif isinstance(value, dict) and not origin:
                        # Check if it's a nested model
                        field_type = field_info.annotation
                        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                            data[field_name] = json.dumps(value)

        return data

    @classmethod
    def from_db_dict(cls, data: dict[str, Any], dialect: str = "postgresql"):
        """
        Create model instance from database dictionary.

        Handles:
        - JSON deserialization for SQLite
        - Type conversion

        Args:
            data: Dictionary from database row
            dialect: "postgresql" or "sqlite"

        Returns:
            Model instance
        """
        # For SQLite, parse JSON strings back to Python objects
        if dialect == "sqlite":
            parsed_data = {}
            for field_name, value in data.items():
                if value is not None and field_name in cls.model_fields:
                    field_info = cls.model_fields[field_name]
                    origin = get_origin(field_info.annotation)

                    # Parse JSON strings back to lists/dicts
                    if origin is list or origin is dict:
                        try:
                            parsed_data[field_name] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            parsed_data[field_name] = value
                    else:
                        parsed_data[field_name] = value
                else:
                    parsed_data[field_name] = value
            data = parsed_data

        return cls(**data)
