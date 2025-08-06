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

class Dirigeant(BaseModel):
    """Model for company directors/managers"""
    # For physical persons
    nom: Optional[str] = None
    prenoms: Optional[str] = None
    annee_de_naissance: Optional[str] = None
    date_de_naissance: Optional[str] = None
    nationalite: Optional[str] = None
    
    # For legal entities
    siren: Optional[str] = None
    denomination: Optional[str] = None
    
    # Common fields
    qualite: Optional[str] = None
    type_dirigeant: Optional[str] = None

    @property
    def display_name(self) -> str:
        if self.denomination:
            return self.denomination
        name = " ".join(filter(None, [self.prenoms, self.nom]))
        return name if name else "(unknown name)"

    @property
    def display_info(self) -> str:
        """Builds the custom display string."""
        if self.denomination:
            # Include siren if present
            siren_part = f" (SIREN: {self.siren})" if self.siren else ""
            return f"{self.display_name}{siren_part} - {self.qualite or 'Sans Qualité'}"
        else:
            parts = [self.display_name]
            if self.date_de_naissance:
                parts.append(f"Né(e) le {self.date_de_naissance}")
            parts.append(self.qualite or 'Sans Qualité')
            return " - ".join(parts)

class FranceCompany(BaseModel):
    Siren: Optional[str] = None
    CompanyName: Optional[str] = None
    Sector: Optional[str] = None
    Address: Optional[str] = None
    CreationDate: Optional[str] = None
    Dirigeants: Optional[str] = None
