import json
import redis

class Database:
    def __init__(self,host,port,username,password):
        self.client = redis.Redis(
            host=host, 
            port=port, 
            username=username, 
            password=password, 
            decode_responses=True
            )

    def get_data(self):
        if not self.client.exists("readme-banner"):
            self.client.set("readme-banner", json.dumps({}))
        raw_json = self.client.get("readme-banner")

        return json.loads(raw_json)

    def set_data(self,data):
        self.client.set("readme-banner", json.dumps(data))


