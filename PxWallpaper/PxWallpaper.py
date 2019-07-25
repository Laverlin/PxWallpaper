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
import PxWallpaperConfig
import subprocess
from azure.storage.blob import BlockBlobService
import random


def main():

    application_path, application_name = GetAppNames()
    logger = SetupLogging(application_path, application_name)

    config = GetConfig(application_path, application_name)
    
    logger.setLevel(config.log_level)

    #imageUrl, photoName, authorName, location = GetBestPhotoInfo(config.consumer_key, config.geo_api_user, config.category_exclude)
    photoFullPath = os.path.join(config.image_path, config.image_file)
    #GetBestPhotoImage(imageUrl, photoFullPath)

    GetPhotoBlob(config.azure_account, config.azure_key,photoFullPath)


    ScreenWidth, ScreenHeight = Adjust2Screen(photoFullPath)

    #fontFullPath = os.path.join(application_path, config.font_name)
    #WriteOverPhoto(fontFullPath, int(config.font_size), photoFullPath, photoName, authorName, location)

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

        ini_fullname = os.path.join(application_path, '{0}.ini'.format(application_name))
        config = PxWallpaperConfig.Config(ini_fullname)
        return config

    except Exception:
        logger.exception("error reading config")
        raise

### getting best photo info form 500px
###
def GetBestPhotoInfo(consumerKey, geoApiUser, category_exclude):

    try:
        logger = logging.getLogger()
        logger.info("download wallpaper info...")

        requestUrl = "https://api.500px.com/v1/photos?feature=popular&image_size=2048&rpp=5&consumer_key={0}".format(consumerKey)
        if category_exclude.lower() != 'none':
            requestUrl += '&exclude={0}'.format(category_exclude)

        response = requests.get(requestUrl)
        if response.status_code != 200:
            raise ConnectionError("Cant get info, status: {0}, text: {1}".format(response.status_code, response.text))

        jsonResult = response.json()
        photoId = 0
        imageUrl = jsonResult['photos'][photoId]['images'][0]['url']
        imageFormat = jsonResult["photos"][photoId]["images"][0]["format"]
        photoName = jsonResult['photos'][photoId]['name']
        authorName = jsonResult['photos'][photoId]['user']['fullname']
        location = jsonResult['photos'][photoId]['location']
        lat = jsonResult['photos'][photoId]['latitude']
        lon = jsonResult['photos'][photoId]['longitude']

        logger.info("photo name : {0}".format(photoName))
        logger.info("author: {0}".format(authorName))
        logger.info("location: {0}, {1}, {2}".format(location, lat, lon))

        if location is None and lat is not None and lon is not None:
            logger.info("get location by geodata")

            requestUrl = "http://api.geonames.org/findNearbyPlaceNameJSON?lat={0}&lng={1}&username={2}".format(lat, lon, geoApiUser)
            response = requests.get(requestUrl)
            if response.status_code != 200:
                logger.exception("Cant get location, status: {0}, text: {1}".format(response.status_code, response.text))
            jsonResult = response.json();
            if len(jsonResult['geonames']) > 0:
                location = "{}, {}".format(jsonResult['geonames'][0]['name'], jsonResult['geonames'][0]['countryName'])
                logger.info("location by geo : {}".format(location))

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
        for i in range(1, 4):
            draw.text((i, i), authorText, (0,0,0), font)
        draw.text((0, 0), authorText, (128,158,128), font)
        if location is not None:
            textWidth, textHeight = font.getsize(authorText)
            locationText = '  at {0}'.format(location)
            for i in range(1, 4):
                draw.text((i, textHeight + fontSize / 2 + i), locationText, (0,0,0), font)
            draw.text((0, textHeight + fontSize / 2), locationText, (128,158,128), font)

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
   # ExecuteShell('icacls {0} /setowner Administrators /T'.format(lockScreenFolder))

### overwrite system cache image of lock screen
###
def WriteLockScreenImage(photoFullPath, screenWidth, screenHeight):

    logger = logging.getLogger()

    systemFolder = 'C:\ProgramData\Microsoft\Windows\SystemData'
    GetPermission(systemFolder)

    imageName = "lockScreen___{0}_{1}_notdimmed.jpg".format(screenWidth, screenHeight)

    userFolders = os.listdir(systemFolder)
    for userFolder in userFolders:
        if userFolder.startswith('S-'):
            lockScreenFolder = os.path.join(systemFolder, userFolder, 'ReadOnly')
            folders = os.listdir(lockScreenFolder)
            for folder in folders:
                if (folder.startswith("LockScreen")):
                    lockScreenFile = os.path.join(lockScreenFolder, folder, imageName)
                    logger.info('write lock screen file : {0}'.format(lockScreenFile))
                    shutil.copyfile(photoFullPath, lockScreenFile)


def GetBlobList(account, key):

    logger = logging.getLogger()

    block_blob_service = BlockBlobService(account_name = account, account_key = key)

    print("\nList blobs in the container")
    generator = block_blob_service.list_blobs("photos")
    for blob in generator:
        print("\t Blob name: " + blob.name)
    count = len(generator.items)
    print("\t count: " + str(count))

    rnd_index = random.randint(0, count-1)
    print("\t index: " + str(rnd_index))
    print("\t random: " + generator.items[rnd_index].name)


def GetPhotoBlob(account, key, path):

    logger = logging.getLogger()

    block_blob_service = BlockBlobService(account_name = account, account_key = key)
    generator = block_blob_service.list_blobs("photos")
    rnd_index = random.randint(0, len(generator.items) - 1)

    logger.info("name: " + generator.items[rnd_index].name + "\t to:" + path)

    block_blob_service.get_blob_to_path("photos", generator.items[rnd_index].name, path)


if __name__ == "__main__":
    main()
