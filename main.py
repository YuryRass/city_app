from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import City
from shemas import CityCreate, SCity
import aiohttp

from config import settings

app = FastAPI()

init_db()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_coordinates(city_name: str):
    async with aiohttp.ClientSession() as session:
        params = {"q": city_name, "key": settings.API_KEY}
        async with session.get(settings.BASE_URL, params=params) as response:
            if response.status == 200:
                data = await response.json()
                coordinates = data["results"][0]["geometry"]
                return coordinates["lat"], coordinates["lng"]
            raise HTTPException(status_code=404, detail="Coordinates not found")


@app.post("/cities/", response_model=SCity)
async def create_city(city: CityCreate, db: Session = Depends(get_db)):
    latitude, longitude = await get_coordinates(city.name)
    print(latitude, longitude)
    db_city = City(name=city.name, latitude=latitude, longitude=longitude)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city


@app.delete("/cities/{city_id}")
def delete_city(city_id: int, db: Session = Depends(get_db)):
    db_city = db.query(City).filter(City.id == city_id).first()
    if db_city is None:
        raise HTTPException(status_code=404, detail="City not found")
    db.delete(db_city)
    db.commit()
    return {"detail": "City deleted"}


@app.get("/cities/", response_model=list[SCity])
def read_cities(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    cities = db.query(City).offset(skip).limit(limit).all()
    return cities


@app.get("/cities/nearest/")
async def get_nearest_cities(
    latitude: float, longitude: float, db: Session = Depends(get_db)
):
    cities = db.query(City).all()
    cities_sorted = sorted(
        cities,
        key=lambda city: (city.latitude - latitude) ** 2
        + (city.longitude - longitude) ** 2,
    )
    return cities_sorted[:2]
