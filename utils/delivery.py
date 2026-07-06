import httpx
import os

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Твоя точка выдачи (Bendi 6, Bali)
ORIGIN_LAT = -8.8020625
ORIGIN_LNG = 115.1985625

# Тариф доставки
DELIVERY_BASE_PRICE = 12000   # до 5 км
DELIVERY_BASE_KM = 5          # базовые км
DELIVERY_PRICE_PER_KM = 3000  # Rp за каждый км сверх базовых


async def get_distance_km(dest_lat: float, dest_lng: float) -> float | None:
    """Получить расстояние в км через Google Maps Distance Matrix API"""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": f"{ORIGIN_LAT},{ORIGIN_LNG}",
        "destinations": f"{dest_lat},{dest_lng}",
        "mode": "driving",
        "key": GOOGLE_MAPS_API_KEY
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10)
            data = resp.json()
            element = data["rows"][0]["elements"][0]
            if element["status"] == "OK":
                distance_m = element["distance"]["value"]
                return round(distance_m / 1000, 1)
    except Exception as e:
        print(f"Google Maps error: {e}")
    return None


def calculate_delivery_cost(distance_km: float) -> int:
    """Рассчитать стоимость доставки"""
    if distance_km <= DELIVERY_BASE_KM:
        return DELIVERY_BASE_PRICE
    extra_km = distance_km - DELIVERY_BASE_KM
    return DELIVERY_BASE_PRICE + round(extra_km) * DELIVERY_PRICE_PER_KM
