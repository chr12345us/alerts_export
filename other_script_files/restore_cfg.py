import json
import requests
import sys

with open(sys.argv[1]) as file:
    jsonData = json.load(file)

for i in jsonData["hits"]["hits"]:
    source = i["_source"]
    r = requests.put("http://localhost:9200/" + i["_index"] + "/_doc/" + i["_id"], json=source, headers={"Content-Type": "application/json"})
    r.raise_for_status()
    print(r.json());
