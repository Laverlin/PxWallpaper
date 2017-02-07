import requests
import json

def main():
    print("let's start")

    result = requests.get("https://api.500px.com/v1/photos?feature=popular&image_size=2048&rpp=1&consumer_key=" + getConsumerKey())
    data = result.json()
    print("photo url: " + data['photos'][0]['images'][0]['url'])
    print("photo format: " + data["photos"][0]["images"][0]["format"])
    print(json.dumps(data, indent = 2))



def getConsumerKey():
    
    with open('config.json') as config:
        consumerKey = json.loads(config.read())
        return consumerKey["authentication"]["consumer_key"]

if __name__ == "__main__":
    main()