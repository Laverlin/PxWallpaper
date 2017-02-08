import requests
import json
import shutil

def main():
    print("let's start")

    jsonResult = requests.get("https://api.500px.com/v1/photos?feature=popular&image_size=2048&rpp=1&consumer_key=" + getConsumerKey()).json()
    imageUrl = jsonResult['photos'][0]['images'][0]['url']
    imageFormat = jsonResult["photos"][0]["images"][0]["format"]

    imageResponse = requests.get(imageUrl, stream = True)
    if imageResponse.status_code == 200:
        with open("todaysBest.jpg", "wb") as imageFile:
            imageResponse.raw.decode_content = True
            shutil.copyfileobj(imageResponse.raw, imageFile)






    print("photo url: {0}".format(imageUrl))

    print("photo format: {0}".format(imageFormat))

    print(json.dumps(jsonResult, indent = 2))



def getConsumerKey():
    
    with open('config.json') as config:
        consumerKey = json.loads(config.read())
        return consumerKey["authentication"]["consumer_key"]

if __name__ == "__main__":
    main()