import sys

output_file = sys.argv[1]
num_clients = int(sys.argv[2])

with open(output_file, "w") as f:
    # Server
    f.write("""name: tp0
services:
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - EXPECTED_CLIENTS={num_clients}
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini
""")

    # Clients
    for i in range(1, num_clients + 1):
        f.write(f"""
  client{i}:
    container_name: client{i}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={i}
      - NOMBRE=Santiago Lionel
      - APELLIDO=Lorca
      - DOCUMENTO=30904465
      - NACIMIENTO=1999-03-17
      - NUMERO=7574
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
      - ./.data/agency-{i}.csv:/data.csv
""")

    # Networks
    f.write("""
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
""")
