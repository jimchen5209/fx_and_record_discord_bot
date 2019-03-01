# -*- coding: utf-8 -*-
import discord
from discord.embeds import Embed
import os
import io
import asyncio
import sys
import time
import logging
import json
import pytz
from datetime import datetime

if os.path.isdir("./logs") == False:
    os.mkdir("./logs")
logpath = "./logs/"+time.strftime("%Y-%m-%d-%H-%M-%S").replace("'", "")
logger = logging.getLogger('discord')
logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler(
    filename=logpath+'-discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

soundData = {}

class Config:
    def __init__(self):
        try:
            with open("config.json", "r") as fs:
                self.__configRaw = json.load(fs)
        except FileNotFoundError:
            print(
                "[Error] Can't load config.json: File not found.\n[Info] Generating empty config...")
            config = {
                "TOKEN": "",
                "Debug": False
            }
            with open("config.json", "w") as fs:
                json.dump(config, fs, indent=2)
            print("\n[Info] Fill your config and try again.")
            exit()
        except json.decoder.JSONDecodeError as e1:
            print("[Error] Can't load config.json: JSON decode error:",
                  e1.args, "\n\n[Info] Check your config format and try again.")
            exit()
        self.token = self.__configRaw["TOKEN"]
        self.debug = self.__configRaw["Debug"]
        self.commandPrefix = self.__configRaw["commandPrefix"]
        return

class ServerConfig:
    __defaultSetting = {
        "timeZone" : "Asia/Taipei",
        "timeText" : "現在時間是 {0}",
        "ttsLang" : "zh_tw",
        "hourFormat" : "12",
        "timeHourly" : False
    }
    def __init__(self):
        try:
            with io.open("data.json", "r", encoding='utf8') as fs:
                self.__dataRaw = json.load(fs)
        except FileNotFoundError:
            with io.open("data.json", "w", encoding='utf8') as fs:
                json.dump({}, fs, indent=2, ensure_ascii=False)
            self.__dataRaw = {}
        except json.decoder.JSONDecodeError as e1:
            print("[Error] Can't load data.json: JSON decode error:",
                  e1.args, "\n\n[Info] Check your data file or reset it and try again.")
            exit()
        return

    def reload(self):
        self.__init__()
        return
    
    def getServerList(self):
        return list(self.__dataRaw)

    def getSetting(self, serverID, setting):
        if serverID not in self.__dataRaw:
            self.__dataRaw[serverID] = self.__defaultSetting
            self.__saveSetting()
        if setting not in self.__dataRaw[serverID]:
            self.__dataRaw[serverID][setting] = self.__defaultSetting[setting]
            self.__saveSetting()
        return self.__dataRaw[serverID][setting]

    def setSetting(self, serverID, setting, value):
        self.__dataRaw[serverID][setting] = value
        self.__saveSetting()
        return

    def __saveSetting(self):
        with io.open("data.json" , "w", encoding='utf8') as fs:
            json.dump(self.__dataRaw, fs, indent=2, ensure_ascii=False)
        return
        

def loadSoundData():
    global soundData
    try:
        with open("sound.json", "r",encoding='utf8') as fs:
            soundData = json.load(fs)
    except FileNotFoundError:
        soundData = {
            "command":{},
            "keyword":{}
        }
    except json.decoder.JSONDecodeError as e1:
        print("[Error] Can't load config.json: JSON decode error:",
            e1.args, "\n\n[Info] Check your config format and try again.")
        soundData = {
            "command":{},
            "keyword":{}
        }
    soundData["help"] = '''{0}help\n{0}join\n{0}leave\n{0}stop\n{0}time\n\nSoundLists:\n'''.format(config.commandPrefix)
    for i in soundData["command"]:
        soundData["help"] += "{0}{1}\n".format(config.commandPrefix,i)
    

config = Config()
discord_client = discord.Client()
discord_token = config.token
ttsUrl = 'https://translate.google.com.tw/translate_tts?ie=UTF-8&q="{0}"&tl={1}&client=tw-ob' #{0} for text {1} for tts language
fmt = {
    "12": "%I:%M %p",
    "24": "%H:%M"
}
playing = {}
loadSoundData()
serverConfig = ServerConfig()

@discord_client.event
async def on_ready():
    clog('Logged in as {0} {1}'.format(
        discord_client.user.name, discord_client.user.id))
    clog('------')


@discord_client.event
async def on_message(message):
    dislog = "[Discord][" + \
        time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"][Info]"
    try:
        dislog = dislog + ' ' + message.author.display_name + '@' + message.author.name + \
            ' in '+message.channel.name + \
            " ("+message.channel.id+') : ' + message.content
    except TypeError:
        dislog = dislog + ' ' + message.author.display_name + \
            '@' + message.author.name+' : ' + message.content
    clog(dislog)
    if (message.author.bot):
        # clog("[Info] Ignoring bot message")
        return
    if (message.content.startswith(config.commandPrefix+"join")):
        if (message.author.voice.voice_channel == None):
            await discord_client.send_message(message.channel, "You are not even in a voice channel")
            return
        if not discord_client.is_voice_connected(message.server):
            await discord_client.join_voice_channel(message.author.voice.voice_channel)
            # if not discord.opus.is_loaded():
            #     discord.opus.load_opus("libopus.so.0")
        else:
            if (discord_client.voice_client_in(message.server).channel == message.author.voice.voice_channel):
                await discord_client.send_message(message.channel, "Already connected")
            else:
                voice = discord_client.voice_client_in(message.server)
                await voice.move_to(message.author.voice.voice_channel)
        return
    elif (message.content.startswith(config.commandPrefix+"leave")):
        if discord_client.is_voice_connected(message.server):
            voice = discord_client.voice_client_in(message.server)
            await voice.disconnect()
        return
    elif (message.content.startswith(config.commandPrefix+"stop")):
        voice = discord_client.voice_client_in(message.server)
        if voice.session_id in playing:
            if (playing[voice.session_id].is_playing()):
                playing[voice.session_id].stop()
            del playing[voice.session_id]
        return
    elif (message.content.startswith(config.commandPrefix+"help")):
        embed = Embed(title="Help", description=soundData["help"],color=7388159)
        await discord_client.send_message(message.channel, "Here you are",embed=embed)
        return
    elif (message.content.startswith(config.commandPrefix+"reload")):
        loadSoundData()
        serverConfig.reload()
        await discord_client.send_message(message.channel, "Reload completed")
        return
    elif (message.content.startswith(config.commandPrefix+"time")):
        cmd = message.content.split(" ", 2)
        if len(cmd) != 1:
            if cmd[1] == "help":
                text = '''`{0}time` - Say the current time
                `{0}time currentSetting` - Show current time announce setting of this server.
                `{0}time tz <timeZone>` - Set the time zone of this server. For example: `Asia/Tokyo`
                For a list of timezone, [Click here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
                `{0}time text <text>` - Set the announce text of this server.
                `{0}time lang <lang>` - Set the google tts language of this server.
                `{0}time hourFormat <12/24>` - Set the hourFormat of this server.
                `{0}time hourly [True/False]` - Set if hourly time announce is enable in this server. No value is to toggle.
                '''.format(config.commandPrefix)
                embed = Embed(title="Help",description=text, color=7388159)
                await discord_client.send_message(message.channel, "Here you are", embed=embed)
                return
            elif cmd[1] == "currentSetting":
                text = '''**Time Zone:** {0}
                **Announce Text:** {1}
                **Announce TTS Language:** {2}
                **Hour Format:** {3}
                **Announce Hourly:** {4}
                '''.format(
                    serverConfig.getSetting(message.server.id, 'timeZone'),
                    serverConfig.getSetting(message.server.id, 'timeText'),
                    serverConfig.getSetting(message.server.id, 'ttsLang'),
                    serverConfig.getSetting(message.server.id, 'hourFormat'),
                    str(serverConfig.getSetting(message.server.id, 'timeHourly'))
                )
                embed = Embed(title="Server Current Setting",
                            description=text, color=7388159)
                await discord_client.send_message(message.channel, "Here you are", embed=embed)
                return
            elif cmd[1] == "tz":
                if len(cmd) == 2:
                    text = '''**Current Time Zone:** {0}

                    **Command usage:** `{1}time tz <timeZone>`
                    '''.format(serverConfig.getSetting(message.server.id, 'timeZone'), config.commandPrefix)
                    embed = Embed(title=None,description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Invalid Command", embed=embed)
                    return
                else:
                    serverConfig.setSetting(message.server.id, 'timeZone', cmd[2])
                    text = "**New Time Zone:** {0}".format(serverConfig.getSetting(message.server.id, 'timeZone'))
                    embed = Embed(title=None, description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Setting Saved", embed=embed)
            elif cmd[1] == "text":
                if len(cmd) == 2:
                    text = '''**Current Announce Text:** {0}

                    **Command usage:** `{1}time text <text>`
                    '''.format(serverConfig.getSetting(message.server.id, 'timeText'), config.commandPrefix)
                    embed = Embed(title=None, description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Invalid Command", embed=embed)
                    return
                else:
                    serverConfig.setSetting(message.server.id, 'timeText', cmd[2])
                    text = "**New Announce Text:** {0}".format(serverConfig.getSetting(message.server.id, 'timeText'))
                    embed = Embed(title=None, description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Setting Saved", embed=embed)
            elif cmd[1] == "lang":
                if len(cmd) == 2:
                    text = '''**Current Announce TTS Language:** {0}

                    **Command usage:** `{1}time lang <lang>`
                    '''.format(serverConfig.getSetting(message.server.id, 'ttsLang'), config.commandPrefix)
                    embed = Embed(title=None, description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Invalid Command", embed=embed)
                    return
                else:
                    serverConfig.setSetting(message.server.id, 'ttsLang', cmd[2])
                    text = "**New Announce TTS Language:** {0}".format(serverConfig.getSetting(message.server.id, 'ttsLang'))
                    embed = Embed(title=None, description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Setting Saved", embed=embed)
            elif cmd[1] == "hourFormat":
                if len(cmd) == 2:
                    text = '''**Current Hour Format:** {0}

                    **Command usage:** `{1}time hourFormat <12/24>`
                    '''.format(serverConfig.getSetting(message.server.id, 'hourFormat'), config.commandPrefix)
                    embed = Embed(title=None, description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Invalid Command", embed=embed)
                    return
                else:
                    if cmd[2] not in ["12", "24"]:
                        text = '''**Current Hour Format:** {0}

                        **Command usage:** `{1}time hourFormat <12/24>`
                        '''.format(serverConfig.getSetting(message.server.id, 'hourFormat'), config.commandPrefix)
                        embed = Embed(title=None, description=text, color=7388159)
                        await discord_client.send_message(message.channel, "Invalid Command", embed=embed)
                    else:
                        serverConfig.setSetting(message.server.id, 'hourFormat', cmd[2])
                        text = "**New Hour Format:** {0}".format(serverConfig.getSetting(message.server.id, 'hourFormat'))
                        embed = Embed(title=None, description=text, color=7388159)
                        await discord_client.send_message(message.channel, "Setting Saved", embed=embed)
                return
            elif cmd[1] == "hourly":
                if len(cmd) == 2:
                    serverConfig.setSetting(message.server.id, 'timeHourly', not serverConfig.getSetting(message.server.id, 'timeHourly'))
                    text = "**New Hour Format:** {0}".format(serverConfig.getSetting(message.server.id, 'timeHourly'))
                    embed = Embed(title=None, description=text, color=7388159)
                    await discord_client.send_message(message.channel, "Setting Saved", embed=embed)
                else:
                    if cmd[2].lower() == "true":
                        serverConfig.setSetting(message.server.id, 'timeHourly', True)
                        text = "**New Hour Format:** {0}".format(serverConfig.getSetting(message.server.id, 'timeHourly'))
                        embed = Embed(title=None, description=text, color=7388159)
                        await discord_client.send_message(message.channel, "Setting Saved", embed=embed)
                    elif cmd[2].lower() == "false":
                        serverConfig.setSetting(message.server.id, 'timeHourly', False)
                        text = "**New Hour Format:** {0}".format(serverConfig.getSetting(message.server.id, 'timeHourly'))
                        embed = Embed(title=None, description=text, color=7388159)
                        await discord_client.send_message(message.channel, "Setting Saved", embed=embed)
                    else:
                        text = '''**Current Announce Hourly:** {0}

                        **Command usage:** `{1}time hourly [True/False]`
                        '''.format(str(serverConfig.getSetting(message.server.id, 'timeHourly')), config.commandPrefix)
                        embed = Embed(title=None, description=text, color=7388159)
                        await discord_client.send_message(message.channel, "Invalid Command", embed=embed)
                return
            else:
                await discord_client.send_message(message.channel, "Unknown command. Try {0}time help.".format(config.commandPrefix))
                return
        await timeAnnounce.announce(message.server.id, message.channel)
        return
        
    for i in soundData["command"]:
        if (message.content.startswith(config.commandPrefix + i)):
            if not discord_client.is_voice_connected(message.server):
                await discord_client.send_message(message.channel, "I'm not in a voice channel, use ~join to let me in.")
            else:
                voice = discord_client.voice_client_in(message.server)
                if voice.session_id in playing:
                    if (playing[voice.session_id].is_playing()):
                        await discord_client.send_message(message.channel, "Nope")
                        return
                player = voice.create_ffmpeg_player(soundData["command"][i])
                playing[voice.session_id] = player
                player.start()
            return
    for i in soundData["keyword"]:
        if (message.content.lower().find(i) != -1):
            if discord_client.is_voice_connected(message.server):
                voice = discord_client.voice_client_in(message.server)
                if voice.session_id in playing:
                    if (playing[voice.session_id].is_playing()):
                        #await discord_client.send_message(message.channel, "Nope")
                        return
                player = voice.create_ffmpeg_player(soundData["keyword"][i])
                playing[voice.session_id] = player
                player.start()
            return

class TimeAnnounce:
    def __init__(self):
        asyncio.ensure_future(self.announceHourly())
    async def announce(self, serverID,channel = None):
        server = discord_client.get_server(serverID)
        if not discord_client.is_voice_connected(server):
            if channel != None:
                await discord_client.send_message(channel, "I'm not in a voice channel, use ~join to let me in.")
            else:
                return False
        else:
            utc = pytz.timezone("UTC")
            utcTime = utc.localize(datetime.utcnow())
            format = fmt[serverConfig.getSetting(serverID, "hourFormat")]
            serverTimeZone = pytz.timezone(
                serverConfig.getSetting(serverID, "timeZone"))
            nowTime = utcTime.astimezone(serverTimeZone)
            text = serverConfig.getSetting(serverID, "timeText").format(nowTime.strftime(format))
            voice = discord_client.voice_client_in(server)
            if voice.session_id in playing:
                if (playing[voice.session_id].is_playing()):
                    if channel != None:
                        await discord_client.send_message(channel, "Nope")
                        return
                    else:
                        pass
            # print(ttsUrl.format(text, serverConfig.getSetting(
            #     serverID, "ttsLang")))
            if channel != None:
                embed = Embed(title=None, description=text, color=7388159)
                await discord_client.send_message(channel, "", embed=embed)
            player = voice.create_ffmpeg_player(ttsUrl.format(
                text, serverConfig.getSetting(serverID, "ttsLang")).replace(" ", "%20"))
            playing[voice.session_id] = player
            player.start()
            return True
    async def announceHourly(self):
        clog("["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "") + "][Info] Hourly AnnounceMent Started")
        while True:
            if time.localtime().tm_sec != 0:
                await asyncio.sleep(3600-(time.localtime().tm_sec + time.localtime().tm_min * 60))
            else:
                await asyncio.sleep(3600)
            clog("["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "") + "][Info] The time is now {0}".format(time.strftime("%H:%M")))
            for i in serverConfig.getServerList():
                if serverConfig.getSetting(i, "timeHourly"):
                    await self.announce(i)

timeAnnounce = TimeAnnounce()

def clog(text):
    print(text)
    log(text)
    return


def log(text):
    if text[0:7] == "[Debug]":
        if config.debug:
            logger = io.open(logpath+"-debug.log", "a", encoding='utf8')
            logger.write(
                "["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"]"+text+"\n")
            logger.close()
        return
    logger = io.open(logpath+".log", "a", encoding='utf8')
    logger.write(text+"\n")
    logger.close()
    return


log("[Logger] If you don't see this file currectly,turn the viewing encode to UTF-8.")
log("[Debug][Logger] If you don't see this file currectly,turn the viewing encode to UTF-8.")
log("[Debug] Bot's TOKEN is "+discord_token)
clog("["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"][Info] Bot has started")
clog("["+time.strftime("%Y/%m/%d-%H:%M:%S").replace("'", "")+"][Info] Listening ...")

discord_client.run(discord_token)
