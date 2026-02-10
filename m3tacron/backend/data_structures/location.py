"""
Location data structure.
"""
import reflex as rx
from typing import Self
from sqlalchemy import JSON, TypeDecorator
from pydantic import BaseModel

class Location(BaseModel):
    """
    Represents a geographical location with normalized city and state.
    """
    city: str | None = None
    country: str | None = None
    continent: str | None = None
    
    @staticmethod
    def _normalize(value: str | None) -> str | None:
        """
        Normalize location string to Title Case and strip whitespace.
        
        Args:
            value: Raw location string.
            
        Returns:
            Normalized string or None.
        """
        if isinstance(value, str):
            cleaned = value.strip().title()
            return cleaned if cleaned else None
        return value

    @classmethod
    def create(cls, city: str | None = None, country: str | None = None, continent: str | None = None) -> Self:
        """
        Factory method to create a Location with normalized values.
        """
        return cls(
            city=cls._normalize(city),
            country=cls._normalize(country),
            continent=cls._normalize(continent)
        )


class LocationType(TypeDecorator):
    """
    SQLAlchemy TypeDecorator to handle Pydantic Location object serialization.
    """
    impl = JSON
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if hasattr(value, "model_dump"): return value.model_dump()
        if hasattr(value, "dict"): return value.dict()
        if isinstance(value, dict): return value
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, dict):
            return Location(**value)
        return value
