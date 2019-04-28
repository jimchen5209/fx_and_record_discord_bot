# -*- coding: utf-8 -*-
import json
import logging
import os
import io

class ServerConfig:
    def __init__(self, timeZone, timeText, timeFormatoClock, timeFormatNormal, ttsLang, timeHourly, timeHourlyPrefixSound, timeHourlySuffixSound, lastVoiceChannel):
        self.timeZone: str= timeZone
        self.timeText: str= timeText
        self.timeFormatoClock: str = timeFormatoClock
        self.timeFormatNormal: str = timeFormatNormal
        self.ttsLang: str= ttsLang
        self.timeHourly: bool = timeHourly
        self.timeHourlyPrefixSound: str = timeHourlyPrefixSound
        self.timeHourlySuffixSound: str = timeHourlySuffixSound
        self.lastVoiceChannel: str = lastVoiceChannel

class Data:
    __defaultSetting = {
        "timeZone": "Asia/Taipei",
        "timeText": "現在時間是 {0}",
        "timeFormatoClock": "%I %p整",
        "timeFormatNormal": "%I:%M %p",
        "ttsLang": "zh_tw",
        "timeHourly": False,
        "timeHourlyPrefixSound": "",
        "timeHourlySuffixSound": "",
        "lastVoiceChannel" : ""
    }
    def __init__(self):
        self.__logger = logging.getLogger("Config")
        logging.basicConfig(
            format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)
        self.__logger.info("Loading Data...")
        if os.path.isfile("./data.json") == False:
            with io.open("./data.json", "w", encoding='utf8') as fs:
                fs.write("{}")
        try:
            with io.open("./data.json", "r", encoding='utf8') as fs:
                self.__dataraw = json.load(fs)
        except json.decoder.JSONDecodeError as e1:
            self.__logger.error(
                "Can't load data.json: JSON decode error:{0}".format(str(e1.args)))
            self.__logger.info("Maybe it's an old data, trying to migrate...")
            try:
                with io.open("./data.json", "r", encoding='utf8') as fs:
                    self.__dataraw = eval(fs.read())
                self.__saveData()
            except SyntaxError:
                self.__logger.error("Can't load data.json: Syntax Error")
                exit()

    def reload(self):
        self.__init__()
        return

    def getServerList(self) -> list:
        return list(self.__dataraw)

    def getData(self,server: str) -> ServerConfig:
        if server not in self.__dataraw:
            self.setData(server)
        try:
            obj = ServerConfig(
                self.__dataraw[server]['timeZone'],
                self.__dataraw[server]['timeText'],
                self.__dataraw[server]['timeFormatoClock'],
                self.__dataraw[server]['timeFormatNormal'],
                self.__dataraw[server]['ttsLang'],
                self.__dataraw[server]['timeHourly'],
                self.__dataraw[server]['timeHourlyPrefixSound'],
                self.__dataraw[server]['timeHourlySuffixSound'],
                self.__dataraw[server]['lastVoiceChannel']
            )
        except KeyError:
            self.__mergeSetting(server)
            obj = ServerConfig(
                self.__dataraw[server]['timeZone'],
                self.__dataraw[server]['timeText'],
                self.__dataraw[server]['timeFormatoClock'],
                self.__dataraw[server]['timeFormatNormal'],
                self.__dataraw[server]['ttsLang'],
                self.__dataraw[server]['timeHourly'],
                self.__dataraw[server]['timeHourlyPrefixSound'],
                self.__dataraw[server]['timeHourlySuffixSound'],
                self.__dataraw[server]['lastVoiceChannel']
            )
        finally:
            return obj

    def setData(self, server: str, **args):
        if server not in self.__dataraw:
            self.__dataraw[server] = self.__defaultSetting.copy()
        else:
            if 'timeZone' in args:
                self.__dataraw[server]['timeZone'] = args['timeZone']
            if 'timeText' in args:
                self.__dataraw[server]['timeText'] = args['timeText']
            if 'timeFormatoClock' in args:
                self.__dataraw[server]['timeFormatoClock'] = args['timeFormatoClock']
            if 'timeFormatNormal' in args:
                self.__dataraw[server]['timeFormatNormal'] = args['timeFormatNormal']
            if 'ttsLang' in args:
                self.__dataraw[server]['ttsLang'] = args['ttsLang']
            if 'timeHourly' in args:
                self.__dataraw[server]['timeHourly'] = args['timeHourly']
            if 'timeHourlyPrefixSound' in args:
                self.__dataraw[server]['timeHourlyPrefixSound'] = args['timeHourlyPrefixSound']
            if 'timeHourlySuffixSound' in args:
                self.__dataraw[server]['timeHourlySuffixSound'] = args['timeHourlySuffixSound']
            if 'lastVoiceChannel' in args:
                self.__dataraw[server]['lastVoiceChannel'] = args['lastVoiceChannel']
        self.__saveData()

    def __mergeSetting(self, server: str):
        newConfig = self.__defaultSetting.copy()
        for i in self.__dataraw[server]:
            if i in newConfig:
                newConfig[i] = self.__dataraw[server][i]
        self.__dataraw[server] = newConfig.copy()
        self.__saveData()

    def __saveData(self):
        with io.open("./data.json", "w", encoding='utf8') as fs:
            json.dump(self.__dataraw, fs, indent=2, ensure_ascii=False)
