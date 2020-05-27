import yaml
import base64
import requests
import json

ordersURL = "https://ssapi.shipstation.com/orders"

# Loading configurations
with open('shipstation.yaml', 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print ("Error while loading YAML.")

apiKey = config['user']
apiSecret = config['token']
apiAuth = "{}:{}".format(apiKey, apiSecret)
apiAuth = base64.b64encode(apiAuth.encode('utf-8'))
apiAuth = "Basic {}".format(str(apiAuth, 'utf-8'))

payload = {}
headers = {
  'Host': 'ssapi.shipstation.com',
  'Authorization': apiAuth
}

request = requests.request("GET", ordersURL, headers=headers, data = payload)

data = json.loads(request.text)

with open('data.json', 'w') as f:
    json.dump(data, f, indent=3)

