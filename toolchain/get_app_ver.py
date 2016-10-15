import urllib.request
import json

store_api = urllib.request.urlopen("https://itunes.apple.com/jp/lookup?id=1016318735")
store_b = store_api.read()
store_j = store_b.decode('utf-8')
store_d = json.loads(store_j)

results_l = store_d.get("results")
results_j = json.dumps(results_l[0])
results_d = json.loads(results_j)

app_ver = results_d['version']

print(app_ver)
