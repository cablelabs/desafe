# Decentralized Secure Aggregation with Failover and Encryption (SAFE)

This is an implementation of the [SAFE](https://arxiv.org/abs/2108.05475) protocol
without a controller. Instead of sending the messages through a pubsub bus,
the messages are sent directly along the chain to public endpoints.

The TLS encryption of http is leveraged for protecting the messages and PKI certs
are used for signing payloads.

# Getting started
Install dependencies:
```
pip3 install -r requirements.txt
```

Generate initial keys:
```
./init.sh
```

Create local data samples, e.g.:
```
mkdir -p data1 && echo 10 > data1/qos
mkdir -p data2 && echo 30 > data2/qos
mkdir -p data3 && echo 4 > data3/qos
mkdir -p data4 && echo 40 > data4/qos
```

Configure endpoints. Create a file called `config`
with first column being the name of the public key file and
second column the endpoint, e.g.:
```
client1.pub http://localhost:8081
client2.pub http://localhost:8082
client3.pub http://localhost:8083
client4.pub http://localhost:8084
```

# Run endpoint services
Each participant will run a endpint service with
```
./dsa x
``` 
where `x` is 1-4 and represents the client id or index on the SAFE chain.

# Run aggregation
To start an aggregation run:
```
 ./agg metric
```
where `metric` can be any local data in the data directory (qos in
the example above).

The output will show which clients responded,
at least three non-initiators need to respond as well as the initiator
for the aggregation to be successful.

The final aggregate is verified to cryptographically prove that the participant
submitted values for the aggregation requested.
