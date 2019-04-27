import json
import logging

class Config:
    def __init__(self, testing=False):
        self.__logger = logging.getLogger("Config")
        logging.basicConfig(
            format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)
        self.__logger.info("Loading Config...")
        if testing:
            self.__logger.info("Testing mode detected, using testing config.")
            self.__configraw = {
                "TOKEN": "",
                "commandPrefix": "~",
                "Debug": False
            }
        else:
            try:
                with open('config.json','r') as fs:
                    self.__configraw = json.load(fs)
            except FileNotFoundError:
                self.__logger.info("Generating empty config...")
                config = {
                    "TOKEN": "",
                    "commandPrefix": "~",
                    "Debug": False
                }
                with open('./config.json', 'w') as fs:
                    json.dump(config, fs, indent=2)
                self.__logger.info("Done!Go fill your config now!")
                exit()
            except json.decoder.JSONDecodeError as e1:
                self.__logger.error(
                    "Can't load config.json: JSON decode error:{0}".format(str(e1.args)))
                self.__logger.error("Check your config format and try again.")
                exit()
        self.TOKEN = self.__configraw['TOKEN']
        self.commandPrefix = self.__configraw['commandPrefix']
        self.Debug = self.__configraw['Debug']

class SoundData:
    def __init__(self):
        self.__logger = logging.getLogger("Sound")
        logging.basicConfig(
            format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)
        self.__logger.info("Loading Sound...")
        try:
            with open("sound.json", "r", encoding='utf8') as fs:
                self.__dataraw = json.load(fs)
        except FileNotFoundError:
            self.__logger.info("Generating empty sound data...")
            self.__dataraw = {
                "command": {},
                "keyword": {},
                "reaction": {}
            }
            self.__save()
        except json.decoder.JSONDecodeError as e1:
            self.__logger.error("Can't load config.json: JSON decode error: {0}".format(str(e1.args)))
            self.__logger.error("Check your config format and try again.")
            self.__dataraw = {
                "command": {},
                "keyword": {},
                "reaction": {}
            }
        if "command" not in self.__dataraw:
            self.__dataraw["command"] = {}
            self.__save()
        if "keyword" not in self.__dataraw:
            self.__dataraw["keyword"] = {}
            self.__save()
        if "reaction" not in self.__dataraw:
            self.__dataraw["reaction"] = {}
            self.__save()
        
            
        
    def getSoundCommandList(self) -> list:
        return list(self.__dataraw["command"])

    def getSoundKeyWordList(self) -> list:
        return list(self.__dataraw["keyword"])

    def getSoundReactionList(self) -> list:
        return list(self.__dataraw["reaction"])

    def getAssetFromCommand(self, sound) -> str:
        return self.__dataraw["command"][sound]

    def getAssetFromKeyWord(self, sound)-> str:
        return self.__dataraw["keyword"][sound]

    def getAssetFromReaction(self, sound)-> str:
        return self.__dataraw["reaction"][sound]

    def __save(self):
        with open('./sound.json', 'w') as fs:
            json.dump(self.__dataraw, fs, indent=2)

    def reload(self):
        self.__init__()
