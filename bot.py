import discord
from discord.embeds import Embed
import os
import io
import asyncio
import sys
import time
import logging
import json


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
    soundData["help"] = '''{0}help\n{0}join\n{0}leave\n{0}stop\n\nSoundLists:\n'''.format(config.commandPrefix)
    for i in soundData["command"]:
        soundData["help"] += "{0}{1}\n".format(config.commandPrefix,i)
    

config = Config()
discord_client = discord.Client()
discord_token = config.token
playing = {}
loadSoundData()

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
        clog("[Info] Ignoring bot message")
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
        await discord_client.send_message(message.channel, "Reload completed")
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
