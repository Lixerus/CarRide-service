Task 3: MSA design from Grid and Cloud course

##Architectural case - Uber
###Decomposition of functional requirements:
  - passenger-service:
      - request or cancell cab
      - add or delete personal informaion
      - cab availability and pricing information
      - payment features
  - driver-service:
      - availability status and current orders
      - car related statuses and information
      - personal data manipulation
      - payment features
  - payment-service:
      - users balances and transaction statuses
      - payment related tasks and management
  - geo-service:
      - all geo information processing and approximations
      - other geo algorythms for pair matching
  - pair-matching-service:
      - finds possible suitable driver for passenger
  - tech-support-service:
      - deals with users complaints
  - storage-service:
      - stores and replicates all nessesary information
##Estimatet traffic.
For 1 million users there would be around 1m * 10 operations from users interacting with ui
and 1 complaint for every 10 rides. Lets say each interactions causes 5 events, meaning
11m * 5 requests => around 600requests per second.

##Design and implement microservice architecture
CarRide-service connects available passenger and available driver.
Driver and passenger can become inactive by cancelling search or alreadymade pair.

CarRide-service consist of 3 microservices connected through RabbiMQ and 2 UIs connected with websockets.
**pairing_service** - responsible for pairing available passenger and driver. Gets messages from `pairingex`
RabbitMQ exchnge through `driver-pair` and `passenger-pair` queues. When pair is ready sends it to **driver-service** through
`order` queue.
**driver-service** - responsible for storing drivers information and current states, so it can correctly dispatch
incoming messages and send messages. Listens to `order` queue in `pairingex` exchange and `driver` queue in `costumerex`. Hosts websocket
server for **driver-web-client**. Send messages to **pairing-service** and **passanger-service**.
**passenger-service** - responsible for storing passenger information and state so it can correctly dispatch incoming
messages and send messages. Listens to `passenger` queue in `customerex`. Hosts websocket server for **passenger-web-client**.
##Diagram
![CarRide-service-digram](https://github.com/Lixerus/CarRide-service/assets/61562096/47711b13-f6c7-4d87-bd51-d4f5cd597021)

##Setup
Docker required.
Run ```console docker-compose up``` in root folder.
RabbitMQ container can setup longer than 30 seconds, in that case service containers need to be restarted.

##Example
![CarRide_service_example](https://github.com/Lixerus/CarRide-service/assets/61562096/0287eae5-6c0e-4efe-bc43-f764302c7965)
