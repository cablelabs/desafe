from flask import Flask, request
import json
import sys
import requests
import random
import os
import signer

app = Flask(__name__)

aggregation_db = {}

MY_KEY = signer.import_key(os.getenv("MY_KEY"))

def get_value(metric):
  client = os.getenv("CLIENT")
  with open(f"data{client}/{metric}") as f:
    return int(f.read())

endpoints = []
pub_keys = []
with open('config') as f:
    c = f.read().split("\n")[:-1]
    for conf in c:
      cols = conf.split(" ")
      endpoints.append(cols[1])
      pub_keys.append(signer.import_key(cols[0]))

def get_previous_key():
  global pub_keys
  index = int(os.getenv("CLIENT"))
  previous_index = index - 1
  if previous_index < 1:
    previous_index = len(pub_keys)
  return pub_keys[previous_index - 1]

def get_failover_key():
  global pub_keys
  index = int(os.getenv("CLIENT"))
  if index == 1:
    previous_index = len(pub_keys)-1
  elif index == 2:
    return None
  else:
    previous_index = index - 2
  return pub_keys[previous_index - 1]

def get_next_endpoint():
  global endpoints
  index = int(os.getenv("CLIENT"))
  next_index = index + 1
  if next_index > len(endpoints):
    next_index = 1  
  return endpoints[next_index - 1]

def get_failover_endpoint():
  global endpoints
  index = int(os.getenv("CLIENT"))
  next_index = index + 2
  if index == len(endpoints):
    return None
  if next_index > len(endpoints):
    next_index = 1  
  return endpoints[next_index - 1]

@app.route("/start_aggregation", methods=['POST'])
def start_aggregation():
  global aggregation_db
  global MY_KEY
  global PREV_KEY
  next_endpoint = get_next_endpoint()
  data = request.get_json(force=True)
  metric = data["metric"]
  value = get_value(metric)
  aggid = random.randint(0,10000)
  mask = random.randint(0,10000)
  value = value + mask
  signature = signer.sign(MY_KEY,f"{value}{aggid}")
  submissions = [ signer.sign(MY_KEY,f"{aggid}") ]
  payload = {"aggid":aggid, "value": value, "metric": metric, "signature": signature, "submissions": submissions}
  aggregation_db[aggid] = mask
  print(f"Calling {next_endpoint}")
  try:
    res = requests.post(f"{next_endpoint}/aggregate",json=payload)
  except:
    next_endpoint = get_failover_endpoint()
    if next_endpoint is None:
      return json.dumps({"error": "Failover endpoint not available"})
    print(f"Calling failover {next_endpoint}")
    payload["submissions"].append(None)
    try:
      res = requests.post(f"{next_endpoint}/aggregate",json=payload)
    except:
      return json.dumps({"error": "Next endpoint not reachable"})
  return res.text

@app.route("/aggregate", methods=['POST'])
def aggregate():
  global aggregation_db
  global MY_KEY
  data = request.get_json(force=True)
  if data["submissions"][-1] is None:
    PREV_KEY = get_failover_key()
    if PREV_KEY is None:
      return json.dumps({"error": "Failover signing key not available"})
  else:
    PREV_KEY = get_previous_key()

  try:
    if not signer.verify(PREV_KEY,f"{data['value']}{data['aggid']}",data["signature"]):
      return json.dumps({"error": "Wrong signature"})
  except:
      return json.dumps({"error": "Invalid signature"})

  aggid = data["aggid"]
  if aggid in aggregation_db:
    mask = aggregation_db[aggid]
    tot = data["value"] - mask
    if len(data["submissions"]) >= 3:
        return json.dumps({"total": tot, "aggid": data["aggid"], "submissions":data["submissions"]})
    else:
      return json.dumps({"error": "Not enough submitters"})
  payload = {}
  payload["aggid"] = aggid
  payload["value"] = data["value"] 
  payload["submissions"] = data["submissions"] 
  payload["submissions"].append(signer.sign(MY_KEY,f"{aggid}")) 
  metric = data["metric"]
  value = get_value(metric)
  payload["value"] += value 
  signature = signer.sign(MY_KEY,f"{payload['value']}{aggid}")
  payload["signature"] = signature 
  payload["metric"] = metric 
  next_endpoint = get_next_endpoint()
  print(f"Calling {next_endpoint}")
  try:
    res = requests.post(f"{next_endpoint}/aggregate",json=payload)
  except:
    next_endpoint = get_failover_endpoint()
    if next_endpoint is None:
      return json.dumps({"error": "Failover endpoint not available"})
    print(f"Calling failover {next_endpoint}")
    payload["submissions"].append(None)
    try:
      res = requests.post(f"{next_endpoint}/aggregate",json=payload)
    except:
      return json.dumps({"error": "Next endpoint not reachable"})
  return res.text

if __name__ == "__main__":
  port = 8077
  if len(sys.argv) > 1:
     port = int(sys.argv[1])
  host_env = os.getenv('BINDHOST')
  if not host_env is None and host_env != "":
    host = host_env
  else:
    host = "127.0.0.1"
  next_endpoint = get_next_endpoint()
  print(f"THIS http://localhost:{port} NEXT {next_endpoint}")
  app.run(host=host, port=port, debug=True, threaded=True)
