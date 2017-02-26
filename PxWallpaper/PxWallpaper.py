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
import subprocess

def main():

    application_path, application_name = GetAppNames()
    logger = SetupLogging(application_path, application_name)

    config = GetConfig(application_path, application_name)
    
    logger.setLevel(config.LogLevel)

    imageUrl, photoName, authorName, location = GetBestPhotoInfo(config.ConsumerKey)
    photoFullPath = os.path.join(config.ImagePath, config.ImageFile)
    GetBestPhotoImage(imageUrl, photoFullPath)

    ScreenWidth, ScreenHeight = Adjust2Screen(photoFullPath)

    fontFullPath = os.path.join(application_path, config.FontName)
    WriteOverPhoto(fontFullPath, config.FontSize, photoFullPath, photoName, authorName, location)

    # set new image as background
    #
    ctypes.windll.user32.SystemParametersInfoW(20, 0, photoFullPath, 1)

    #set new image as lock screen
    #
    WriteLockScreenImage(photoFullPath, ScreenWidth, ScreenHeight)

    logger.info("done.")

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

    except Exception:
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
        location = jsonResult['photos'][0]['location']

        logger.info("photo name : {0}".format(photoName))
        logger.info("author: {0}".format(authorName))
        logger.info("location: {0}".format(location))

    except Exception:
        logger.exception("error getting photo info")
        raise

    return imageUrl, photoName, authorName, location

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
            
    except Exception:
        logger.exception("error download photo")
        raise

### Write info over image 
###
def WriteOverPhoto(fontFullPath, fontSize, photoFullPath, photoName, authorName, location):

    try:
        logger = logging.getLogger()

        font = ImageFont.truetype(fontFullPath, fontSize)
        image = Image.open(photoFullPath)
        draw = ImageDraw.Draw(image)
        authorText = '"{0}" by {1}'.format(photoName, authorName)
        draw.text((3, 3), authorText, (0,0,0), font)
        draw.text((0, 0), authorText, (128,158,128), font)
        if location is not None:
            textWidth, textHeight = fontDark.getsize(authorText)
            locationText = 'at {0}'.format(location)
            draw.text((3, textHeight + 10), locationText, (0,0,0), font)
            draw.text((0, textHeight + 7), locationText, (128,158,128), font)

       # draw = ImageDraw.Draw(image)
        image.save(photoFullPath)
    except Exception:
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

        return screenWidth, screenHeight

    except Exception:
        logger.exception("error photo postprocess")
        raise

### execute OS command. Use to take ownership on system folder
###
def ExecuteShell(command):
    
    logger = logging.getLogger()

    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    retval = process.wait()
    if retval != 0:
        logger.error('execute shell error:{0}, retvalue:{1}'.format(process.stdout.read(), retval))

### Get permission of system folders to change lock screen
###
def GetPermission(lockScreenFolder):

    logger = logging.getLogger()
    logger.debug('Get permissions on lock screen folder')

    ExecuteShell('takeown /F {0} /R /D Y'.format(lockScreenFolder))
    ExecuteShell('icacls {0}\* /inheritance:e /T'.format(lockScreenFolder))
    ExecuteShell('icacls {0} /setowner Administrators /T'.format(lockScreenFolder))

### overwrite system cache image of lock screen
###
def WriteLockScreenImage(photoFullPath, screenWidth, screenHeight):

    logger = logging.getLogger()

    lockScreenFolder = 'C:\ProgramData\Microsoft\Windows\SystemData\S-1-5-18\ReadOnly'
    imageName = "lockScreen___{0}_{1}_notdimmed.jpg".format(screenWidth, screenHeight)

    GetPermission(lockScreenFolder)

    folders = os.listdir(lockScreenFolder)
    for folder in folders:
        if (folder.startswith("LockScreen")):
            lockScreenFile = os.path.join(lockScreenFolder, folder, imageName)
            logger.info('write lock screen file : {0}'.format(lockScreenFile))
            shutil.copyfile(photoFullPath, lockScreenFile)


if __name__ == "__main__":
    main()
