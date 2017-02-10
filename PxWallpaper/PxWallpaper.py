import requests
import json
import shutil
import os
import sys
import ctypes


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

    ctypes.windll.user32.SystemParametersInfoW(20, 0, photoFullName , 1)

    print("done")



def GetConfig():

    # determine if application is a script file or frozen exe
    #
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        config_name = os.path.basename(sys.executable).replace('.exe','.config')
    elif __file__:
        application_path = os.path.dirname(__file__)
        config_name = os.path.basename(__file__).replace('.py','.config')

    config_path = os.path.join(application_path, config_name)

    print(config_path)

    with open(config_name) as config:
        config = json.loads(config.read())
        return config["authentication"]["consumer_key"], config["image_path"], config["image_file"]

if __name__ == "__main__":
    main()