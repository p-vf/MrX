# MrX
Service for sharing geolocation where the clients can choose the accuracy of their location.

![Shhhh, its a secret](mrx.png)

## How to run

- [uv](https://docs.astral.sh/uv/) must be installed on the system. To install `uv`, follow the instructions on [this website](https://docs.astral.sh/uv/getting-started/installation/).

- Clone this repository

- Change your working directory to the folder `./code` relative to the root of this project.

- To start the server, run `uv run server`
  - if you want to start the server on localhost, run `uv run server --hostip localhost`

- If the server and the client run on different machines, the created server certificate (located in `./code/keys/mrx-server.crt`) must be copied to the same location in the client.

- To start the client, run `uv run client --hostip <server-ip>`