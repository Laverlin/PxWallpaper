import requests
import json
import shutil
import os


def main():
    print("let's start")

    consumer_key, image_path, image_file = GetConfig()
    requestUrl = "https://api.500px.com/v1/photos?feature=popular&image_size=2048&rpp=1&consumer_key={0}".format(consumer_key)
    jsonResult = requests.get(requestUrl).json()
    imageUrl = jsonResult['photos'][0]['images'][0]['url']
    imageFormat = jsonResult["photos"][0]["images"][0]["format"]

    photoFullName = os.path.join(image_path, image_file)
    imageResponse = requests.get(imageUrl, stream = True)
    if imageResponse.status_code == 200:
        with open(photoFullName, "wb") as imageFile:
            imageResponse.raw.decode_content = True
            shutil.copyfileobj(imageResponse.raw, imageFile)






    print("photo url: {0}".format(imageUrl))

    print("photo format: {0}".format(imageFormat))

    print(json.dumps(jsonResult, indent = 2))



def GetConfig():
    
    with open('config.json') as config:
        config = json.loads(config.read())
        return config["authentication"]["consumer_key"], config["image_path"], config["image_file"]

if __name__ == "__main__":
    main()