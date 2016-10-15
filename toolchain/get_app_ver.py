import urllib.request
import json

store_api = urllib.request.urlopen("https://itunes.apple.com/jp/lookup?id=1016318735")
store_b = store_api.read()
store_j = store_b.decode('utf-8')
store_d = json.loads(store_j)

results_l = store_d.get("results")
app_ver = results_l[0]['version']

print(app_ver)
