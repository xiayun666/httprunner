import requests
a=requests.get('https://generator.swagger.io/api/swagger.json').json()
print(a)