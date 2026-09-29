Project: Test and Document Consul Connect Performance Impact on Microservices Communication

Final project structure
```text
consul-connect-performance/
│
├── service-a/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── service-b/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── consul/
│   ├── server.hcl
│   ├── service-a.hcl
│   └── service-b.hcl
│
├── tests/
│   ├── baseline-results.txt
│   ├── consul-connect-results.txt
│   └── resource-results.txt
│
├── screenshots/
│   ├── consul-ui.png
│   ├── services.png
│   └── health-checks.png
│
└── README.md

```
1. Project objective

The goal is to measure the performance difference between:

Test A — Without Consul Connect
```text
ApacheBench
     |
     v
Service A :8080
     |
     | Direct HTTP
     v
Service B :8080
```


Test B — With Consul Connect
```text
ApacheBench
     |
     v
Service A :8080
     |
     v
127.0.0.1:22000
     |
     v
Service A Connect Proxy :21001
     |
     | mTLS
     v
Service B Connect Proxy :21000
     |
     v
Service B :8080

```

We then compare:

Requests per second<br>
Average response time<br>
Failed requests<br>
95th percentile latency<br>
Maximum latency<br>
CPU usage<br>
Memory usage

Part 1 — Prerequisites

macOS<br>
Docker Desktop<br>
Terminal<br>
Python<br>
ApacheBench (ab)

Check Docker:

docker --version

Check ApacheBench:
ab -V

Check Python:

python3 --version

Part 2 — Create the project
Open Terminal.

Create the project:

mkdir -p ~/Documents/consul-connect-performance<br>
cd ~/Documents/consul-connect-performance


pwd

/Users/jissvarghese/Documents/consul-connect-performance

Part 3 — Create project directories

Run:

mkdir -p service-a service-b consul tests screenshots

```text
consul-connect-performance/
│
├── service-a/
│   ├── app.py
│   └── Dockerfile
│
├── service-b/
│   ├── app.py
│   └── Dockerfile
│
├── consul/
│   ├── service-a.json
│   ├── service-a-connect.json
│   ├── service-b.json
│   └── service-b-connect.json
│
└── tests/
```
Create Docker network

docker network create performance-network
docker network ls

Part 4 — Create Service B

Service B is the backend microservice.

Create the file:<br>
cd ~/Documents/consul-connect-performance/service-b

code app.py
```text
from flask import Flask

app = Flask(__name__)

@app.route("/health")
def health():
    return "Service B is healthy"

@app.route("/api")
def api():
    return "Response from Service B"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

Service B provides: GET /health (for heaith checking)

And:
returns: Response from Service B

The application listens on: 0.0.0.0:8080

Part 5 — Create Service B Dockerfile

Run:

code Dockerfile<br>
```text
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir flask

COPY app.py .

EXPOSE 8080

CMD ["python", "app.py"]

```

Build Service B

docker build -t performance-service-b:latest .<br>
verify:<br>
docker images | grep performance-service-b

Run Service B

docker run -d --name service-b --network performance-network performance-service-b:latest

docker ps

Test Service B<br>
docker exec service-b python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health').read().decode())"

Service B is healthy

docker exec service-b python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/api').read().decode())"

Response from ServiceB

docker ps

docker exec service-b python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health').read().decode())"

Part 6 — Create Service A

Service A is the frontend microservice.

Initially, it will communicate directly with Service B for the baseline test.

cd ~/Documents/consul-connect-performance/service-a

Create:

code app.py
```text
from flask import Flask
import requests

app = Flask(__name__)

SERVICE_B_URL = "http://service-b:8080"

@app.route("/health")
def health():
    return "Service A is healthy"

@app.route("/api")
def api():
    response = requests.get(
        f"{SERVICE_B_URL}/api",
        timeout=5
    )
    return f"Service A received: {response.text}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


```
   Part 7 — Create Service A Dockerfile

code Dockerfile

    FROM python:3.12-slim

    WORKDIR /app

    RUN pip install --no-cache-dir flask requests

    COPY app.py .

    EXPOSE 8080

    CMD ["python", "app.py"]

    ```

Part 8 — Build Docker images for Service A
docker build -t performance-service-a:latest .

docker images | grep performance-service

Remove any old Service A container

docker rm -f service-a 2>/dev/null

Start Service A

docker run -d \
  --name service-a \
  --network performance-network \
  -p 8080:8080 \
  performance-service-a:latest

  docker ps<br>
Test Service A health

curl http://localhost:8080/health

Expected: Service A is healthy

Test Service A → Service B

curl http://localhost:8080/api

Service A received: Response from Service B

It proves:
```text
Mac
 ↓
Service A
 ↓
Docker network
 ↓
Service B

```
is working.

Verify Service B directly from Service A

Run:

docker exec service-a python -c "import urllib.request; print(urllib.request.urlopen('http://service-b:8080/api').read().decode())"


Response from Service B

This confirms Docker DNS can resolve:

service-b from inside Service A.

Check the Docker network

docker network inspect performance-network


Current architecture

At this point we have:


                    Mac
                     │
                     │ :8080
                     ▼
             ┌───────────────┐
             │   Service A   │
             │   Flask :8080 │
             └───────┬───────┘
                     │
                     │ HTTP
                     │ service-b:8080
                     ▼
             ┌───────────────┐
             │   Service B   │
             │   Flask :8080 │
             └───────────────┘

No Consul Connect yet.

This is our baseline/direct communication architecture.



docker ps<br>
curl http://localhost:8080/health<br>
curl http://localhost:8080/api

Baseline Performance Test

Now we need to measure the performance without Consul Connect.

Check ApacheBench<br>
ab -V

ab -n 1000 -c 10 http://localhost:8080/api > Base_1000_10.txt

ab -n 1000 -c 10 http://localhost:8080/api > Base_1000_10_2.txt

ab -n 1000 -c 10 http://localhost:8080/api > Base_1000_10_3.txt


The first test also confirms:

Failed requests: 0<br>
Requests/sec: 609.40<br>
Mean time/request: 16.410 ms<br>
50th percentile: 15 ms<br>
95th percentile: 20 ms<br>
Maximum: 54 ms

| Test       | Requests | Concurrency | Requests/sec | Mean latency | Failed |
| ---------- | -------: | ----------: | -----------: | -----------: | -----: |
| Baseline 1 |     1000 |          10 |        609.40|        16.410|      0 |
| Baseline 2 |     1000 |          10 |        614.13|        16.283|      0 |
| Baseline 3 |     1000 |          10 |        617.91|        16.184|      0 |


| Run        | Requests/sec | Mean time/request | 95th percentile | Failed |
| ---------- | -----------: | ----------------: | --------------: | -----: |
| Baseline 1 |       609.40 |         16.410 ms |           20 ms |      0 |
| Baseline 2 |       614.13 |         16.283 ms |           21 ms |      0 |
| Baseline 3 |       617.91 |         16.184 ms |           20 ms |      0 |


Average throughput:

613.81 requests/sec

Average mean request time:

16.292 ms

Check Docker resource usage

docker stats --no-stream service-a service-b


resource snapshot

| Container |   CPU |    Memory |
| --------- | ----: | --------: |
| Service A | 0.03% | 28.62 MiB |
| Service B | 0.03% | 32.69 MiB |


docker network inspect performance-network

curl http://localhost:8080/api

Service A received: Response from Service B

Install Consul

Now we start the actual service mesh portion.

docker images | grep consul

docker pull hashicorp/consul:1.20

docker images | grep consul


Remove any old Consul container

docker rm -f consul 2>/dev/null

Check port 8500

lsof -nP -iTCP:8500 -sTCP:LISTEN

Start Consul

docker run -d \
  --name consul \
  --network performance-network \
  -p 8500:8500 \
  -p 8600:8600/udp \
  hashicorp/consul:1.20 \
  consul agent \
  -server \
  -bootstrap-expect=1 \
  -ui \
  -client=0.0.0.0

  docker ps

  docker exec consul consul members

  curl http://localhost:8500/v1/status/leader

  172.18.0.4:8300

  Verify consul UI

  http://localhost:8500

  should see

  . Services<br>
  . Nodes<br>
  . Key/Value<br>
  . ACLs<br>
  . Intentions

  curl http://localhost:8500/v1/status/leader

  Register Service B

  Before we register it, let's verify the container's IP address. 
  Run:

  docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' service-b

  172.18.0.2

  And it listens on: 8080

  So we'll register it with Consul as:

  service-b → 172.18.0.2:8080

  Create the Service B Consul registration

  mkdir -p consul

  Then create the registration file:

code consul/service-b.json
```text

{
  "service": {
    "name": "service-b",
    "id": "service-b",
    "address": "172.18.0.2",
    "port": 8080,
    "check": {
      "http": "http://172.18.0.2:8080/health",
      "interval": "10s",
      "timeout": "2s"
    }
  }
}

```
Register the service with Consul

docker cp consul/service-b.json consul:/consul/service-b.json

docker exec consul cat /consul/service-b.json

Register Service B

docker exec consul consul services register /consul/service-b.json

Check that Consul sees Service B
curl http://localhost:8500/v1/catalog/service/service-b

Check Service B health through Consul

curl "http://localhost:8500/v1/health/service/service-b?passing=true"

Service A registration

docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' service-a

172.18.0.3

Create Service A registration

code consul/service-a-json

ls -l consul/service-a.json

docker cp consul/service-a.json consul:/consul/service-a.json

docker exec consul cat /consul/service-a.json

Register Service A

docker exec consul consul services register /consul/service-a.json

curl http://localhost:8500/v1/catalog/service/service-a

curl "http://localhost:8500/v1/health/service/service-a?passing=true"

Update Service B to enable Connect

We currently registered Service B without a Connect proxy:
```text
Service B
172.18.0.2:8080
    │
    └── Connect: not enabled yet
```
We'll first create a new Service B registration file with a Connect sidecar definition.

    code consul/service-b-connect.json
```text
    
{
  "service": {
    "name": "service-b",
    "id": "service-b",
    "address": "172.18.0.2",
    "port": 8080,
    "check": {
      "http": "http://172.18.0.2:8080/health",
      "interval": "10s",
      "timeout": "2s"
    },
    "connect": {
      "sidecar_service": {
        "proxy": {
          "local_service_address": "172.18.0.2",
          "local_service_port": 8080
        }
      }
    }
  }
}
```
Copy the updated configuration into Consul

docker cp consul/service-b-connect.json consul:/consul/service-b-connect.json

Register the updated Service B configuration

docker exec consul consul services register /consul/service-b-connect.json

Verify Connect is enabled

curl http://localhost:8500/v1/catalog/service/service-b

List all Consul services

curl http://localhost:8500/v1/catalog/services

Check the sidecar details

curl http://localhost:8500/v1/catalog/service/service-b-sidecar-proxy

Start Service B's built-in Connect proxy

docker run -d \
  --name service-b-proxy \
  --network container:service-b \
  -e CONSUL_HTTP_ADDR=http://consul:8500 \
  hashicorp/consul:1.20 \
  consul connect proxy \
  -sidecar-for=service-b \
  -http-addr=http://consul:8500

  docker ps --filter name=service-b-proxy

  docker logs service-b-proxy

  Verify the proxy health

  curl "http://localhost:8500/v1/health/service/service-b-sidecar-proxy?passing=true"

  Register Service A's Connect sidecar

  code consul/service-a-connect.json
```text
  {
  "service": {
    "name": "service-a",
    "id": "service-a",
    "address": "172.18.0.3",
    "port": 8080,
    "check": {
      "http": "http://172.18.0.3:8080/health",
      "interval": "10s",
      "timeout": "2s"
    },
    "connect": {
      "sidecar_service": {
        "proxy": {
          "local_service_address": "172.18.0.3",
          "local_service_port": 8080,
          "upstreams": [
            {
              "destination_name": "service-b",
              "local_bind_address": "0.0.0.0",
              "local_bind_port": 22000
            }
          ]
        }
      }
    }
  }
}
```
docker cp consul/service-a-connect.json consul:/consul/service-a-connect.json

docker exec consul consul services register /consul/service-a-connect.json

curl http://localhost:8500/v1/catalog/services

Find the A-sidecar port

curl http://localhost:8500/v1/catalog/service/service-a-sidecar-proxy

Start the Service A Connect proxy

docker run -d \
  --name service-a-proxy \
  --network container:service-a \
  -e CONSUL_HTTP_ADDR=http://consul:8500 \
  hashicorp/consul:1.20 \
  consul connect proxy \
  -sidecar-for=service-a \
  -http-addr=http://consul:8500

  docker ps --filter name=service-a-proxy

  docker logs service-a-proxy

  One thing is still missing: your Python Service A application is still calling:

  SERVICE_B_URL = "http://service-b:8080" change to SERVICE_B_URL = "http://127.0.0.1:22000"

  because 22000 is the local upstream listener created by the Service A proxy.


Rebuild Service A

docker build -t performance-service-a:latest service-a

Stop and remove only the old Service A container

docker stop service-a

docker rm service-a

Start the new Service A container

docker run -d \
  --name service-a \
  --network performance-network \
  -p 8080:8080 \
  performance-service-a:latest

  docker ps --filter name=service-a

  docker ps -a --filter name=service-a-proxy

  docker logs service-a-proxy

  docker rm -f service-a-proxy

  docker run -d \
  --name service-a-proxy \
  --network container:service-a \
  -e CONSUL_HTTP_ADDR=http://172.18.0.4:8500 \
  hashicorp/consul:1.20 \
  consul connect proxy \
  -sidecar-for=service-a \
  -http-addr=http://172.18.0.4:8500

  docker ps --filter name=service-a-proxy

  docker logs --tail 20 service-a-proxy

  Proxy loaded config and ready to serve

  docker exec service-a sh -c 'python -c "import urllib.request; print(urllib.request.urlopen(\"http://127.0.0.1:22000/api\", timeout=5).read().decode())"'

  Response from Service B

  curl http://localhost:8080/api

  Service A received: Response from Service B

  Verify both Connect proxies are passing

  curl "http://localhost:8500/v1/health/service/service-a-sidecar-proxy?passing=true"

  curl "http://localhost:8500/v1/health/service/service-b-sidecar-proxy?passing=true"

  Run the first mesh performance test

  ab -n 1000 -c 10 http://localhost:8080/api > Mesh_1000_10.txt

  ab -n 1000 -c 10 http://localhost:8080/api > Mesh_1000_10_2.txt

  ab -n 1000 -c 10 http://localhost:8080/api > Mesh_1000_10_3.txt

  Performance comparison

  | Metric            | Direct / Baseline | Consul Connect |  Difference |
| ----------------- | ----------------: | -------------: | ----------: |
| Requests          |             1,000 |          1,000 |           — |
| Concurrency       |                10 |             10 |           — |
| Requests/sec      |        **613.81** |     **452.66** | **−26.25%** |
| Mean time/request |     **16.292 ms** |   **22.12 ms** | **+35.77%** |
| Failed requests   |             **0** |          **0** |   No change |
| 95th percentile   |         **20 ms** |      **32 ms** |    **+60%** |
| Maximum latency   |         **57 ms** |     **104 ms** | **+82.46%** |


1. Throughput decreased

613.81 → 452.66 requests/sec

That's approximately a 26.25% reduction in throughput.

2. Average latency increased

16.292 ms → 22.12 ms

That's approximately a 35.77% increase in mean request time.

3. Reliability remained the same

Baseline failures: 0
Connect failures:  0

So all 1,000 mesh requests completed successfully.

4. Higher-percentile latency increased

The 95th percentile went from:

20 ms → 32 ms

With the test configuration of 1,000 requests and concurrency 10, Consul Connect reduced measured throughput from 613.81 requests/sec to 452.66 requests/sec and increased mean request latency from 16.292 ms to 22.12 ms. Both tests completed with zero failed requests.

resource utilization

docker stats --no-stream service-a service-a-proxy service-b service-b-proxy consul


Current mesh resource usage

| Component               |   CPU |    Memory | PIDs |
| ----------------------- | ----: | --------: | ---: |
| Service A               | 0.03% | 32.18 MiB |    1 |
| Service A Connect proxy | 0.15% | 32.67 MiB |   14 |
| Service B               | 0.03% | 38.54 MiB |    1 |
| Service B Connect proxy | 0.06% | 34.38 MiB |   14 |
| Consul                  | 0.88% | 61.87 MiB |   14 |



Proxy overhead

For the two application proxies together:

CPU:
0.15% + 0.06% = 0.21%

Memory:
32.67 + 34.38 = 67.05 MiB

The proxies therefore add about 0.21% CPU and 67.05 MiB of container memory at the instant captured by docker stats.

For comparison, your earlier baseline snapshot had:

Service A: 0.03% CPU, 28.62 MiB
Service B: 0.03% CPU, 32.69 MiB

However, these are point-in-time snapshots, not measurements averaged over the entire ApacheBench run, so we shouldn't treat them as precise benchmark averages.




grep -E "Time taken|Complete requests|Failed requests|Requests per second|Time per request" Mesh_1000_10.txt Mesh_1000_10_2.txt Mesh_1000_10_3.txt

Collect detailed latency results

Run:

grep -E "50%|66%|75%|80%|90%|95%|98%|99%|100%" Mesh_1000_10.txt Mesh_1000_10_2.txt Mesh_1000_10_3.txt

grep -E "50%|66%|75%|80%|90%|95%|98%|99%|100%" Base_1000_10.txt Base_1000_10_2.txt Base_1000_10_3.txt

Check Docker resource usage

docker stats --no-stream service-a service-b

With Connect:

docker stats --no-stream service-a service-a-proxy service-b service-b-proxy consul

Final architecture

                       ┌───────────────────┐
                       │   ApacheBench     │
                       │ 1000 requests     │
                       │ concurrency = 10  │
                       └─────────┬─────────┘
                                 │
                                 ▼
                    ┌───────────────────────┐
                    │     Service A         │
                    │       :8080           │
                    │   Python + Flask      │
                    └──────────┬────────────┘
                               │
                               │ HTTP
                               ▼
                       ┌──────────────┐
                       │    :22000    │
                       │   upstream   │
                       └──────┬───────┘
                              │
                              ▼
                    ┌───────────────────────┐
                    │ Service A Connect     │
                    │ Proxy :21001          │
                    └──────────┬────────────┘
                               │
                               │ mTLS
                               ▼
                    ┌───────────────────────┐
                    │ Service B Connect     │
                    │ Proxy :21000          │
                    └──────────┬────────────┘
                               │
                               ▼
                    ┌───────────────────────┐
                    │     Service B         │
                    │       :8080           │
                    │   Python + Flask      │
                    └───────────────────────┘

                    ┌───────────────────────┐
                    │       Consul          │
                    │       :8500           │
                    │ Service Discovery     │
                    │ Health Checks         │
                    │ Connect / mTLS        │
                    └───────────────────────┘


