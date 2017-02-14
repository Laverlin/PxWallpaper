import requests
import json
import shutil
import os
import sys
import ctypes
import logging
import PIL
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import Config

def main():

    application_path, application_name = GetAppNames()
    logger = SetupLogging(application_path, application_name)

    config = GetConfig(application_path, application_name)
    
    logger.setLevel(config.LogLevel)

    imageUrl, photoName, authorName = GetBestPhotoInfo(config.ConsumerKey)
    photoFullPath = os.path.join(config.ImagePath, config.ImageFile)
    GetBestPhotoImage(imageUrl, photoFullPath)

    Adjust2Screen(photoFullPath)

    fontFullPath = os.path.join(application_path, config.FontName)
    WriteOverPhoto(fontFullPath, photoFullPath, photoName, authorName)

    ctypes.windll.user32.SystemParametersInfoW(20, 0, photoFullPath, 1)

    logger.info("done")

### get path to executable file and name of executable file
###
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

### Setup logging infrastructure
###
def SetupLogging(application_path, application_name):

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logFileHandler = logging.FileHandler(os.path.join(application_path, '{0}.log'.format(application_name)))
    logFileHandler.setFormatter(logFormatter)
    logger.addHandler(logFileHandler)

    logConsoleHandler = logging.StreamHandler()
    logConsoleHandler.setFormatter(logFormatter) 
    logger.addHandler(logConsoleHandler)
    return logger

### getting data from config file
###
def GetConfig(application_path, application_name):

    try:
        logger = logging.getLogger()
        config_fullname = os.path.join(application_path, '{0}.config'.format(application_name))

        with open(config_fullname) as configFile:
            jsonData = json.loads(configFile.read())
            config = Config.AsConfig(jsonData)
            return config;

    except Exception as e:
        logger.exception("error reading config")
        raise

### getting best photo info form 500px
###
def GetBestPhotoInfo(consumer_key):

    try:
        logger = logging.getLogger()
        logger.info("download wallpaper info...")

        requestUrl = "https://api.500px.com/v1/photos?feature=popular&image_size=2048&rpp=1&consumer_key={0}".format(consumer_key)
        response = requests.get(requestUrl)
        if response.status_code != 200:
            raise ConnectionError("Cant get info, status: {0}, text: {1}".format(response.status_code, response.text))

        jsonResult = response.json()
        imageUrl = jsonResult['photos'][0]['images'][0]['url']
        imageFormat = jsonResult["photos"][0]["images"][0]["format"]
        photoName = jsonResult['photos'][0]['name']
        authorName = jsonResult['photos'][0]['user']['fullname']

        logger.info("photo name : {0}".format(photoName))
        logger.info("author: {0}".format(authorName))

    except Exception as e:
        logger.exception("error getting photo info")
        raise

    return imageUrl, photoName, authorName

### Download photo
###
def GetBestPhotoImage(imageUrl, photoFullPath):

    try:
        logger = logging.getLogger()
        logger.debug("get image: {0}".format(imageUrl))
        imageResponse = requests.get(imageUrl, stream = True)
        if imageResponse.status_code != 200:
            raise ConnectionError("can not download photo, status:{0}, text:{1}".format(imageResponse.status_code, imageResponse.text))

        with open(photoFullPath, "wb") as imageFile:
            imageResponse.raw.decode_content = True
            shutil.copyfileobj(imageResponse.raw, imageFile)
            
    except Exception as e:
        logger.exception("error download photo")
        raise

### Write info over image 
###
def WriteOverPhoto(fontFullPath, photoFullPath, photoName, authorName):

    try:
        logger = logging.getLogger()

        fontDark = ImageFont.truetype(fontFullPath, 24)
        fontLight = ImageFont.truetype(fontFullPath, 24)
        image = Image.open(photoFullPath)
        draw = ImageDraw.Draw(image)
        draw.text((3, 3), '"{0}" by {1}'.format(photoName, authorName), (0,0,0), fontDark)
        draw.text((0, 0), '"{0}" by {1}'.format(photoName, authorName), (128,158,128), fontLight)
        draw = ImageDraw.Draw(image)
        image.save(photoFullPath)
    except Exception as e:
        logger.exception("error write over")
        raise

### Make image appropriate size to fit in screen
###
def Adjust2Screen(photoFullPath):

    try:
        logger = logging.getLogger()

        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        screenWidth, screenHeight = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        logger.debug("screen width: {0}, height: {1}".format(screenWidth, screenHeight))

        screenImage = Image.new("RGB", (screenWidth, screenHeight), (0, 0, 0))
        photoImage = Image.open(photoFullPath)

        ratio = min(screenWidth / photoImage.width, screenHeight / photoImage.height)
        newWidth = int(photoImage.width * ratio)
        newHeight = int(photoImage.height * ratio)
        logger.debug("resize: original ({0}x{1}), ratio ({2}), new ({3}x{4})"
                     .format(photoImage.width, photoImage.height, ratio, newWidth, newHeight))
        photoImage = photoImage.resize((newWidth, newHeight), Image.LANCZOS)

        screenImage.paste(photoImage, (int((screenWidth - newWidth) / 2 ), int((screenHeight - newHeight) / 2)))
        screenImage.save(photoFullPath)

    except Exception as e:
        logger.exception("error photo postprocess")
        raise


if __name__ == "__main__":
    main()