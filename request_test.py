import requests


'''#url = 'http://localhost:8080'
url = 'https://www.w3schools.com/python/demopage.php'
d = {'key1': 'value1', 'key2': 'value2'}
r = requests.post(url, data=d)
print(r.text)'''

'''import os
import requests

os.environ['NO_PROXY'] = '127.0.0.1'
r = requests.get('http://127.0.0.1:5000')
print(r.content)'''

import json
path = 'F:\\test_github\\Simple Shadow SimpleMarket-v00 .txt'
# Opening JSON file
f = open(path, )

# returns JSON object as
# a dictionary
data = json.load(f)

# Iterating through the json
# list
for key,val in data['bidstacks'].items():
    print(key, val)
print(data)
# Closing file
f.close()


