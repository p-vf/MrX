# 📌 Project Notes

## 🗓️ Deadlines

- **COMMIT:** 05.06 – 18:00  
- **MISC:** 05.06 – 23:59  
- **GPS:** 06.06 – 23:59  
- **FINAL DEADLINE:** 12.06 – 12:00  

---

# TODO

Add set own accuracy / depth level and store in state
area per depth level for update spacial

---

# 🖥️ GUI

## Features
- Add friend button  
- Friend list:
  - Remove friend  
  - Set accuracy  
  - Adapt set accuracy (max (100m^2) ----------|--------- min (1000m^2))
- Add friend request


# 💻 Client

## Client → Server Messages

- `update area [<quad_1>, ..., <quad_n>]`
- `add friend [<name>]`
- `remove friend [<name>]`
- `accept friend [<name>, <ans>]`
- `set accuracy [<name>, <depth_lvl>]`

## State Handling
- Store latest path  
- Store GPS stub object  
- Continuously request location updates from GPS stub  

---

# 🌐 Server

## Server → Client Messages

- `send spatialPart [<sp_type: int>, <param_1>, ..., <param_n>]`
- `add friend [<name_from>]`
- `remove friend [<name_from>]`
- `accept friend [<name_from>, <ans>]`
- `update user area [<name>, <path>]`

## Server Responsibilities

- Store which users each client can see + accuracy level in DB  
- Store path in DB  
- Maintain map: `username → connection`  
- Store friend requests for offline users in DB
- Implement DoS protection  
- Optional: 2FA

---

# 📡 GPS Stub

- Generate random positions using Perlin noise  

---

# 🔄 Pipelines

## GUI → Client

- `add friend [<name>]` I want to add friend: `<name>`
- `remove friend [<name>]` I want to remove friend: `<name>`
- `accept request [<name>, <ans>]` I want to accept friend request from friend: `<name>`
- `set accuracy [<name>, <depth_lvl>]` I want to set the accuracy for friend: `<name>` to level: `<depth_lvl>`

## Model → GUI

- `add friend [<name>]` Add friend with name: `<name>`
- `remove friend [<name>]` Remove friend with name: `<name>`
- `request received [<name_from>]` I got a friend request from friend: `<name_from>`
- `request response [<name_from>, <ans>]` I got an answer from my friend request from friend: `<name>` with answer: `<ans>`
- `spacial info [<min area>, <max area>]` update the info for the accuracy sliders