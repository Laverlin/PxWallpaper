class Config(object):
    """configuration data"""

    def __init__(self, consumerKey, imagePath, imageFile, fontName, logLevel):
        self.ConsumerKey = consumerKey
        self.ImagePath = imagePath
        self.ImageFile = imageFile
        self.LogLevel = logLevel
        self.FontName = fontName

import json

def AsConfig(jsonData):

    return Config(jsonData["authentication"]["consumer_key"], jsonData["image_path"], jsonData["image_file"], 
                  jsonData["font_name"], jsonData["log_level"])


