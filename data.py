# -*- coding: utf-8 -*-
import io
import json
import logging
import os


class ServerConfig:
    def __init__(self, time_zone, time_text, time_format_oclock, time_format_normal, tts_lang, time_hourly,
                 time_hourly_prefix_sound, time_hourly_suffix_sound, last_voice_channel):
        self.timeZone: str = time_zone
        self.timeText: str = time_text
        self.timeFormatoClock: str = time_format_oclock
        self.timeFormatNormal: str = time_format_normal
        self.ttsLang: str = tts_lang
        self.timeHourly: bool = time_hourly
        self.timeHourlyPrefixSound: str = time_hourly_prefix_sound
        self.timeHourlySuffixSound: str = time_hourly_suffix_sound
        self.lastVoiceChannel: str = last_voice_channel


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
        "lastVoiceChannel": ""
    }

    def __init__(self):
        self.__logger = logging.getLogger("Config")
        logging.basicConfig(
            format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)
        self.__logger.info("Loading Data...")
        if not os.path.isfile("./data.json"):
            with io.open("./data.json", "w", encoding='utf8') as fs:
                fs.write("{}")
        try:
            with io.open("./data.json", "r", encoding='utf8') as fs:
                self.__data_raw = json.load(fs)
        except json.decoder.JSONDecodeError as e1:
            self.__logger.error(
                "Can't load data.json: JSON decode error:{0}".format(str(e1.args)))
            self.__logger.info("Maybe it's an old data, trying to migrate...")
            try:
                with io.open("./data.json", "r", encoding='utf8') as fs:
                    self.__data_raw = eval(fs.read())
                self.__saveData()
            except SyntaxError:
                self.__logger.error("Can't load data.json: Syntax Error")
                exit()

    def reload(self):
        self.__init__()
        return

    def getServerList(self) -> list:
        return list(self.__data_raw)

    def getData(self, server: str) -> ServerConfig:
        if server not in self.__data_raw:
            self.setData(server)
        obj = None
        try:
            obj = ServerConfig(
                self.__data_raw[server]['timeZone'],
                self.__data_raw[server]['timeText'],
                self.__data_raw[server]['timeFormatoClock'],
                self.__data_raw[server]['timeFormatNormal'],
                self.__data_raw[server]['ttsLang'],
                self.__data_raw[server]['timeHourly'],
                self.__data_raw[server]['timeHourlyPrefixSound'],
                self.__data_raw[server]['timeHourlySuffixSound'],
                self.__data_raw[server]['lastVoiceChannel']
            )
        except KeyError:
            self.__mergeSetting(server)
            obj = ServerConfig(
                self.__data_raw[server]['timeZone'],
                self.__data_raw[server]['timeText'],
                self.__data_raw[server]['timeFormatoClock'],
                self.__data_raw[server]['timeFormatNormal'],
                self.__data_raw[server]['ttsLang'],
                self.__data_raw[server]['timeHourly'],
                self.__data_raw[server]['timeHourlyPrefixSound'],
                self.__data_raw[server]['timeHourlySuffixSound'],
                self.__data_raw[server]['lastVoiceChannel']
            )
        finally:
            return obj

    def setData(self, server: str, **args):
        if server not in self.__data_raw:
            self.__data_raw[server] = self.__defaultSetting.copy()
        else:
            if 'timeZone' in args:
                self.__data_raw[server]['timeZone'] = args['timeZone']
            if 'timeText' in args:
                self.__data_raw[server]['timeText'] = args['timeText']
            if 'timeFormatoClock' in args:
                self.__data_raw[server]['timeFormatoClock'] = args['timeFormatoClock']
            if 'timeFormatNormal' in args:
                self.__data_raw[server]['timeFormatNormal'] = args['timeFormatNormal']
            if 'ttsLang' in args:
                self.__data_raw[server]['ttsLang'] = args['ttsLang']
            if 'timeHourly' in args:
                self.__data_raw[server]['timeHourly'] = args['timeHourly']
            if 'timeHourlyPrefixSound' in args:
                self.__data_raw[server]['timeHourlyPrefixSound'] = args['timeHourlyPrefixSound']
            if 'timeHourlySuffixSound' in args:
                self.__data_raw[server]['timeHourlySuffixSound'] = args['timeHourlySuffixSound']
            if 'lastVoiceChannel' in args:
                self.__data_raw[server]['lastVoiceChannel'] = args['lastVoiceChannel']
        self.__saveData()

    def __mergeSetting(self, server: str):
        new_config = self.__defaultSetting.copy()
        for i in self.__data_raw[server]:
            if i in new_config:
                new_config[i] = self.__data_raw[server][i]
        self.__data_raw[server] = new_config.copy()
        self.__saveData()

    def __saveData(self):
        with io.open("./data.json", "w", encoding='utf8') as fs:
            json.dump(self.__data_raw, fs, indent=2, ensure_ascii=False)
