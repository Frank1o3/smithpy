from api import api
from requests import get

url = api.search("sodium", loaders=["fabric"], game_versions=["1.21.10"], project_type="mod")

res = get(url)

print(res.json())