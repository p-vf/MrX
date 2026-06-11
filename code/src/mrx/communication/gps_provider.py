from abc import ABC, abstractmethod
import random
import numpy as np
import time
import threading

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

class GpsStub():
  def __init__(self, client):
    self.client = client
    self.rng  = np.random.default_rng(4)
    self.current_location = self.get_location()
    self.params = (0, 0.01)
    self.kill_thread = threading.Event()
  
  def start_moving(self):
    t = threading.Thread(target=self.move_loop)
    t.start()
  
  def move_loop(self):
    while not self.kill_thread.is_set():
      self.step()
      self.client.handle_gps(self.current_location)
      time.sleep(0.1)
    
  def kill(self):
    self.kill_thread.set()

  def get_location(self):
    return (self.rng.uniform(low=46.2, high= 47.2), self.rng.uniform(low=7.2, high= 8.2))

  def step(self):
    m, v = self.params
    delta = (self.rng.normal(m, v), self.rng.normal(m, v))
    self.current_location = (self.current_location[0] + delta[0], self.current_location[1] + delta[1])

gps = RandomSwissGPS()

citygps = RandomSwissCityGPS()

print(f" Your stubbed gps location: {gps.get_location()}")
print(f" GPS location near a city: {citygps.get_location_near_city(0.02)}")