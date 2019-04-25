# -*- coding: utf-8 -*-
import pytz
import asyncio
import discord
import logging
import time
from datetime import datetime
from discord.ext.commands import Bot
from data import Data
from config import SoundData

class TimeAnnounce:
    # {0} for text {1} for tts language
    __ttsUrl = 'https://translate.google.com.tw/translate_tts?ie=UTF-8&q="{0}"&tl={1}&client=tw-ob'

    def __init__(self, bot: Bot, data: Data, soundData: SoundData):
        self.__logger = logging.getLogger("Config")
        logging.basicConfig(
            format="[%(asctime)s][%(levelname)s][%(name)s] %(message)s", level=logging.INFO)
        self.__logger.info("Loading Time Announce...")
        self.__bot = bot
        self.__data = data
        self.__soundData = soundData
        asyncio.ensure_future(self.announceHourly())

    async def announce(self, serverID: str, channelID: str="", waitForSound: bool = False) -> bool:
        server = self.__bot.get_guild(int(serverID))
        config = self.__data.getData(serverID)
        if channelID != "":
            channel = self.__bot.get_channel(int(channelID))
        else:
            channel = None
        voice = server.voice_client
        if voice is None:
            if channel != None:
                await channel.send("I'm not in a voice channel, use ~join to let me in.")
            else:
                return False
        else:
            if voice.is_playing() and not waitForSound:
                if channel != None:
                    await self.__bot.send_message(channel, "Nope")
            sound = config.timeHourlyPrefixSound
            if sound != "":
                while voice.is_playing():
                    await asyncio.sleep(1)
                voice.play(discord.FFmpegPCMAudio(
                    self.__soundData.getAssetFromCommand(sound)))
            utc = pytz.timezone("UTC")
            utcTime = utc.localize(datetime.utcnow())
            serverTimeZone = pytz.timezone(config.timeZone)
            nowTime = utcTime.astimezone(serverTimeZone)
            if nowTime.minute == 0:
                text = config.timeText.format(nowTime.strftime(config.timeFormatoClock))
            else:
                text = config.timeText.format(nowTime.strftime(config.timeFormatNormal))
            if channel != None:
                embed = discord.Embed(
                    title=None, 
                    description=config.timeText.format(nowTime.strftime(config.timeFormatNormal)), 
                    color=7388159
                    )
                await channel.send(embed=embed)
            while voice.is_playing():
                await asyncio.sleep(1)
            voice.play(discord.FFmpegPCMAudio(self.__ttsUrl.format(
                text, config.ttsLang).replace(" ", "%20")))
            sound = config.timeHourlySuffixSound
            if sound != "":
                while voice.is_playing():
                    await asyncio.sleep(1)
                voice.play(discord.FFmpegPCMAudio(
                    self.__soundData.getAssetFromCommand(sound)))
            return True

    async def flashNickName(self):
        pass
        
    async def announceHourly(self):
        self.__logger.info("Hourly Announcement Started")
        while True:
            if time.localtime().tm_sec != 0:
                await asyncio.sleep(3600-(time.localtime().tm_sec + time.localtime().tm_min * 60))
            else:
                await asyncio.sleep(3600)
            self.__logger.info("The time is now {0}".format(time.strftime("%H:%M")))
            for i in self.__data.getServerList():
                if self.__data.getData(i).timeHourly:
                    await self.announce(i, waitForSound = True)
