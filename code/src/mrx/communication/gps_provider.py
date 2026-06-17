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
    self.rng = np.random.default_rng()
    self.params = (0, 0.01)
    self.current_location = self.get_location()
    self.new_location = self.get_location()
    self.kill_thread = threading.Event()
    self.next_steps = []
    self.next_time = []
  
  def start_moving(self):
    t = threading.Thread(target=self.move_loop)
    t.start()
  
  def move_loop(self):
    while not self.kill_thread.is_set():
      if len(self.next_steps) == 0:
        self.current_location = self.new_location
        time.sleep(1)
        self.find_next_steps()
        
      self.client.handle_gps(self.next_steps.pop(0))
      time.sleep(self.next_time.pop(0))

  def find_next_steps(self):
    self.new_location = self.get_location()

    ox, oy = self.current_location
    nx, ny = self.new_location

    x_dist = nx-ox
    y_dist = ny-oy
    abs_dist = np.abs(x_dist)

    steps = (int)(np.ceil(abs_dist/0.015))

    x_lin = np.linspace(0,x_dist,steps)
    y_lin = np.linspace(0,y_dist,steps)

    self.next_steps = [((ox + dx), (oy + dy)) for dx, dy in zip(x_lin, y_lin)]

    t_lin = np.linspace(0,abs_dist,steps)
    mid = abs_dist/2
    wait_time = 1 - (0.8*(steps/(1+steps)))
    
    self.next_time = [float(self.strech(x, mid, wait_time)) for x in t_lin]

  def strech(self, value, mid, shortest_wait):
    return (1/(mid*mid + shortest_wait)) * (value-mid) * (value-mid) + shortest_wait
    
  def kill(self):
    self.kill_thread.set()

  def get_location(self):
    return (self.rng.uniform(low=46.2, high= 47.2), self.rng.uniform(low=7.2, high= 8.2))

if __name__ == "__main__":
  gps = GpsStub(None)
  gps.start_moving()
  time.sleep(1)
  gps.kill()