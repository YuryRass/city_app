from pydantic import BaseModel


class CityCreate(BaseModel):
    name: str


class SCity(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float

    class Config:
        from_attributes = True
