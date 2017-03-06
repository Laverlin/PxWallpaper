from configparser import SafeConfigParser

class Config(object):

    def __init__(self, *file_names):

        parser = SafeConfigParser()
        parser.optionxform = str  # make option names case sensitive

        found = parser.read(file_names)
        if not found:
            raise ValueError('No config file found!')

        for name in parser.sections():
            self.__dict__.update(parser.items(name))
        
        if not 'category_exclude' in dir(self):
            self.category_exclude = 'none'

