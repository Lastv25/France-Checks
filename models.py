from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel

class FranceCompany(BaseModel):
    Siren: Optional[str] = None
    CompanyName: Optional[str] = None
    Sector: Optional[str] = None
    Address: Optional[str] = None
    CreationDate: Optional[str] = None
