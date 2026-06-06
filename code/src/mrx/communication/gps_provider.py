from abc import ABC, abstractmethod
import random

class GPSProvider(ABC):

  @abstractmethod
  def get_location(self):
    pass

class RandomSwissGPS(GPSProvider):

  def get_location(self):
    return (
      random.uniform(45.8, 47.9), # latitude 45.8 - 47.9
      random.uniform(5.9, 10.5),  # longitude 5.9 - 10.5
    )

class RandomSwissCityGPS():

  SWISS_CITIES = [
    (47.3769, 8.5417),  # Zürich
    (46.9480, 7.4474),  # Bern
    (46.2044, 6.1432),  # Genf
    (47.5596, 7.5886),  # Basel
    (46.5197, 6.6323),  # Lausanne
  ]

  def get_location_near_city(self, radius_deg):
    lat, lon = random.choice(self.SWISS_CITIES)

    return (
      lat + random.uniform(-radius_deg, radius_deg),
      lon + random.uniform(-radius_deg, radius_deg)
    )


gps = RandomSwissGPS()

citygps = RandomSwissCityGPS()

print(f" Your stubbed gps location: {gps.get_location()}")
print(f" GPS location near a city: {citygps.get_location_near_city(0.02)}")