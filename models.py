from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel

class FranceCompany(BaseModel):
    Siren: str
    CompanyName: str
    Sector: str
    Address: str
    CreationDate: str
