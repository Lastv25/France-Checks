from typing import Dict, List, Literal, Optional, Union
import json

from pydantic import BaseModel, field_validator

class Jugement(BaseModel):
    type: Optional[str] = None
    famille: Optional[str] = None
    nature: Optional[str] = None
    date: Optional[str] = None
    complementJugement: Optional[str] = None
    
    @classmethod
    def from_json_string(cls, json_string: str) -> 'Jugement':
        """Parse a JSON string into a Jugement object"""
        if not json_string:
            return cls()
        try:
            data = json.loads(json_string)
            return cls(**data)
        except (json.JSONDecodeError, TypeError) as e:
            # Return empty model if parsing fails
            return cls()

class FranceCompany(BaseModel):
    Siren: Optional[str] = None
    CompanyName: Optional[str] = None
    Sector: Optional[str] = None
    Address: Optional[str] = None
    CreationDate: Optional[str] = None
