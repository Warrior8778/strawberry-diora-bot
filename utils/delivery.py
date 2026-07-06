import httpx
import os
import re

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Твоя точка выдачи (Bendi 6, Bali)
ORIGIN_LAT = -8.8020625
ORIGIN_LNG = 115.1985625

# Тариф доставки
DELIVERY_BASE_PRICE = 12000
DELIVERY_BASE_KM = 5
DELIVERY_PRICE_PER_KM = 2700


async def resolve_google_maps_url(url: str) -> tuple[float, float] | tuple[None, None]:
    """Получить координаты из короткой ссылки Google Maps"""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            resp = await client.get(url)
            final_url = str(resp.url)

        # Ищем координаты в URL формата @lat,lng
        match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))

        # Ищем координаты в формате /place/.../@lat,lng
        match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', final_url)
        if match:
            return float(match.group(1)), float(match.group(2))

        # Пробуем Geocoding API если есть адрес в URL
        match = re.search(r'place/([^/]+)/', final_url)
        if match and GOOGLE_MAPS_API_KEY:
            place = match.group(1).replace('+', ' ')
            coords = await geocode_address(place)
            if coords:
                return coords

    except Exception as e:
        print(f"URL resolve error: {e}")
    return None, None


async def geocode_address(address: str) -> tuple[float, float] | tuple[None, None]:
    """Получить координаты по адресу через Geocoding API"""
    if not GOOGLE_MAPS_API_KEY:
        return None, None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address + ", Bali", "key": GOOGLE_MAPS_API_KEY}
            )
            data = resp.json()
            if data["status"] == "OK":
                loc = data["results"][0]["geometry"]["location"]
                return loc["lat"], loc["lng"]
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None, None


async def get_distance_km(dest_lat: float, dest_lng: float) -> float | None:
    """Получить расстояние в км через Google Maps Distance Matrix API"""
    if not GOOGLE_MAPS_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json",
                params={
                    "origins": f"{ORIGIN_LAT},{ORIGIN_LNG}",
                    "destinations": f"{dest_lat},{dest_lng}",
                    "mode": "driving",
                    "key": GOOGLE_MAPS_API_KEY
                }
            )
            data = resp.json()
            element = data["rows"][0]["elements"][0]
            if element["status"] == "OK":
                import math; return math.ceil(element["distance"]["value"] / 1000)
    except Exception as e:
        print(f"Distance Matrix error: {e}")
    return None


def calculate_delivery_cost(distance_km: float) -> int:
    if distance_km <= DELIVERY_BASE_KM:
        return DELIVERY_BASE_PRICE
    extra_km = distance_km - DELIVERY_BASE_KM
    return int(DELIVERY_BASE_PRICE + extra_km * DELIVERY_PRICE_PER_KM)


def is_google_maps_url(text: str) -> bool:
    return any(x in text for x in ["maps.app.goo.gl", "maps.google.com", "goo.gl/maps"])
