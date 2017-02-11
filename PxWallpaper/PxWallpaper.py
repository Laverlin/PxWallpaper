import requests
import json
import shutil
import os
import sys
import ctypes
import logging


def main():

    # setup logging
    #
    application_path, application_name = GetAppNames()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logFileHandler = logging.FileHandler(os.path.join(application_path, '{0}.log'.format(application_name)))
    logFileHandler.setFormatter(logFormatter)
    logger.addHandler(logFileHandler)

    logConsoleHandler = logging.StreamHandler()
    logConsoleHandler.setFormatter(logFormatter) 
    logger.addHandler(logConsoleHandler)

    # request best photo info
    #
    logger.info("begin download new wallpaper...")

    consumer_key, image_path, image_file = GetConfig()
    requestUrl = "https://api.500px.com/v1/photos?feature=popular&image_size=2048&rpp=1&consumer_key={0}".format(consumer_key)
    jsonResult = requests.get(requestUrl).json()
    imageUrl = jsonResult['photos'][0]['images'][0]['url']
    imageFormat = jsonResult["photos"][0]["images"][0]["format"]
    photoName = jsonResult['photos'][0]['name']
    authorName = jsonResult['photos'][0]['user']['fullname']

    logger.info("photo name : {0}".format(photoName))
    logger.info("author: {0}".format(authorName))

    # download image
    #
    photoFullName = os.path.join(image_path, image_file)
    imageResponse = requests.get(imageUrl, stream = True)
    if imageResponse.status_code == 200:
        with open(photoFullName, "wb") as imageFile:
            imageResponse.raw.decode_content = True
            shutil.copyfileobj(imageResponse.raw, imageFile)

    # refresh background picture
    #
    ctypes.windll.user32.SystemParametersInfoW(20, 0, photoFullName , 1)

    logger.info("done")



def GetConfig():

    application_path, application_name = GetAppNames()
    config_fullname = os.path.join(application_path, '{0}.config'.format(application_name))

    with open(config_fullname) as config:
        config = json.loads(config.read())
        return config["authentication"]["consumer_key"], config["image_path"], config["image_file"]


def GetAppNames():

    # determine if application is a script file or frozen exe and return name
    #
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        application_name = os.path.basename(sys.executable).replace('.exe','')
    elif __file__:
        application_path = os.path.dirname(__file__)
        application_name = os.path.basename(__file__).replace('.py','')
    return application_path, application_name

if __name__ == "__main__":
    main()