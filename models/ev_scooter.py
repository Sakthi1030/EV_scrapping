from pydantic import BaseModel

class EVScooter(BaseModel):
    """
    Represents the data structure for an electric scooter.
    """
    name: str
    speed: str
    range: str
    rating: float
    reviews: int
    price: str
    emi: str
    extra_details: str
