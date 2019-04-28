# -*- coding: utf-8 -*-
import asyncio
import io
import json
import logging
import os
import sys
import time
import discord
from datetime import datetime
from discord.ext import commands
import locale

locale.setlocale(locale.LC_CTYPE, '')

from config import Config
from data import Data
from config import SoundData
from timeAnnounce import TimeAnnounce

#Setup logging
if os.path.isdir("./logs") == False:
    os.mkdir("./logs")
logpath = "./logs/"+time.strftime("%Y-%m-%d-%H-%M-%S").replace("'", "")
logformat = "[%(asctime)s][%(levelname)s][%(name)s] %(message)s"
logging.root.name = "VoiceLog"
logger = logging.getLogger()
logging.basicConfig(format=logformat, level=logging.INFO)
handler = logging.FileHandler(
    filename=logpath+'.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(logformat))
logger.addHandler(handler)

#Setup Config
if len(sys.argv) != 1:
    if sys.argv[1] == 'test':
        config = Config(True)
    else:
        raise SyntaxError("Invaild command santax: {0}".format(sys.argv[1]))
else:
    config = Config()

data = Data()
soundData = SoundData()
discord_client = commands.Bot(command_prefix=config.commandPrefix, help_command = None)
timeAnnounce = TimeAnnounce(discord_client, data, soundData)

@discord_client.event
async def on_ready():
    logger.info('Logged in as {0} {1}'.format(
        discord_client.user.name, discord_client.user.id))

@discord_client.event
async def on_reaction_add(reaction, user):
    voice = reaction.message.guild.voice_client
    if reaction.count == 1:
        if not reaction.custom_emoji:
            if reaction.emoji in soundData.getSoundReactionList():
                if voice != None:
                    if not voice.is_playing():
                        voice.play(discord.FFmpegPCMAudio(
                            soundData.getAssetFromReaction(reaction.emoji)))
        else:
            if reaction.emoji.name in soundData.getSoundReactionList():
                if voice != None:
                    if not voice.is_playing():
                        voice.play(discord.FFmpegPCMAudio(
                            soundData.getAssetFromReaction(reaction.emoji.name)))
    return

@discord_client.event
async def on_voice_state_update(member, before, after):
    voiceState = after
    if voiceState == None:
        voiceState = before
        if voiceState == None:
            return
    server = voiceState.channel.guild
    voice = server.voice_client
    if before != None and after != None:
        if voice != None:
            if before.channel.id == voice.channel.id:
                voiceState = before
            elif after.channel.id == voice.channel.id:
                voiceState = after
        elif data.getData(str(server.id)).lastVoiceChannel != "":
            if data.getData(str(server.id)).lastVoiceChannel == str(before.channel.id):
                voiceState = before
            elif data.getData(str(server.id)).lastVoiceChannel == str(after.channel.id):
                voiceState = after
    no_user = True
    for i in voiceState.channel.members:
        if not i.bot:
            no_user == False
            break
    if no_user:
        if voice != None:
            if voiceState.channel.id == voice.channel.id:
                data.setData(str(server.id), lastVoiceChannel = str(voiceState.channel.id))
                await voice.disconnect()
    else:
        if voice == None:
            if data.getData(str(server.id)).lastVoiceChannel == str(voiceState.channel.id):
                await voice.connect
                data.setData(str(server.id), lastVoiceChannel="")
    pass

@discord_client.command()
async def help(ctx):
    if ctx.guild == None:
        await ctx.send('This bot is not avaliable for private chat.')
        return
    text = "[f]{0}\n\nSoundLists:\n[f]{1}".format(
        "\n[f]".join(["help", "join", "leave", "stop", "time"]),
        "\n[f]".join(soundData.getSoundCommandList())
    ).replace("[f]", config.commandPrefix)
    embed = discord.Embed(title="Help", description=text, color=7388159)
    await ctx.send("Here you are", embed=embed)
    return

@discord_client.command()
async def join(ctx):
    if ctx.guild == None:
        await ctx.send('This bot is not avaliable for private chat.')
        return
    voice = ctx.author.voice.channel
    if voice == None:
        await ctx.send("You are not even in a voice channel")
    else:
        if ctx.guild.voice_client == None:
            await voice.connect()
            data.setData(str(ctx.guild.id), lastVoiceChannel="")
        else:
            if ctx.guild.voice_client.channel == voice:
                await ctx.send("Already connected")
            else:
                await ctx.guild.voice_client.move_to(voice)
    return

@discord_client.command()
async def leave(ctx):
    if ctx.guild == None:
        await ctx.send('This bot is not avaliable for private chat.')
        return
    voice = ctx.guild.voice_client
    if voice != None:
        await voice.disconnect()
    return

@discord_client.command()
async def reload(ctx):
    if ctx.guild == None:
        await ctx.send('This bot is not avaliable for private chat.')
        return
    soundData.reload()
    await ctx.send("Reload Complete")
    return

@discord_client.command()
async def stop(ctx):
    if ctx.guild == None:
        await ctx.send('This bot is not avaliable for private chat.')
        return
    voice = ctx.guild.voice_client
    if voice != None:
        if voice.is_playing:
            voice.stop()

@discord_client.command(name = "time")
async def timeFunc(ctx, *args):
    if ctx.guild == None:
        await ctx.send('This bot is not avaliable for private chat.')
        return
    arg = " ".join(args)
    cmd = arg.split(" ", 1)
    if len(args) != 0:
        if cmd[0] == "help":
            text = '''`{0}time` - Say the current time
            `{0}time currentSetting` - Show current time announce setting of this server.
            `{0}time tz <timeZone>` - Set the time zone of this server. For example: `Asia/Tokyo`
            For a list of timezone, [Click here](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
            `{0}time text <text>` - Set the announce text of this server.
            `{0}time format <normal|oclock> <text>` - Set time format
            `{0}time lang <lang>` - Set the google tts language of this server.
            `{0}time hourly [True/False]` - Set if hourly time announce is enable in this server. No value is to toggle.
            `{0}time hourlyPrefix <sound|remove>` - Set hourly time announce sound.
            `{0}time hourlySuffix <sound|remove>` - Set hourly time announce sound.
            '''.format(config.commandPrefix)
            embed = discord.Embed(title="Help", description=text, color=7388159)
            await ctx.send("Here you are", embed=embed)
            return
        elif cmd[0] == "currentSetting":
            settings = data.getData(str(ctx.guild.id))
            text = '''**Time Zone:** {0}
            **Announce Text:** {1}
            **Time Format Normal:** {2}
            **Time Format o'clock:** {3}
            **Announce TTS Language:** {4}
            **Announce Hourly:** {5}
            **Hourly Prefix Sound:** {6}
            **Hourly Suffix Sound:** {7}
            '''.format(
                settings.timeZone,
                settings.timeText,
                settings.timeFormatNormal,
                settings.timeFormatoClock,
                settings.ttsLang,
                str(settings.timeHourly),
                settings.timeHourlyPrefixSound,
                settings.timeHourlySuffixSound
            )
            embed = discord.Embed(title="Server Current Setting",
                            description=text, color=7388159)
            await ctx.send("Here you are", embed=embed)
            return
        elif cmd[0] == "tz":
            settings = data.getData(str(ctx.guild.id))
            if len(cmd) == 1:
                text = '''**Current Time Zone:** {0}

                **Command usage:** `{1}time tz <timeZone>`
                '''.format(settings.timeZone, config.commandPrefix)
                embed = discord.Embed(title=None, description=text, color=7388159)
                await ctx.send("Invalid Command", embed=embed)
                return
            else:
                data.setData(str(ctx.guild.id), timeZone=cmd[1])
                text = "**New Time Zone:** {0}".format(
                    data.getData(str(ctx.guild.id)).timeZone)
                embed = discord.Embed(title=None, description=text, color=7388159)
                await ctx.send("Setting Saved", embed=embed)
        elif cmd[0] == "text":
            settings = data.getData(str(ctx.guild.id))
            if len(cmd) == 1:
                text = '''**Current Announce Text:** {0}

                **Command usage:** `{1}time text <text>`
                '''.format(settings.timeText, config.commandPrefix)
                embed = discord.Embed(title=None, description=text, color=7388159)
                await ctx.send("Invalid Command", embed=embed)
                return
            else:
                data.setData(str(ctx.guild.id), timeText=cmd[1])
                text = "**New Announce Text:** {0}".format(
                    data.getData(str(ctx.guild.id)).timeText)
                embed = discord.Embed(title=None, description=text, color=7388159)
                await ctx.send("Setting Saved", embed=embed)
        elif cmd[0] == "format":
            
            cmd1 = arg.split(" ", 2)
            settings = data.getData(str(ctx.guild.id))
            textInvalid = '''**Current Time Format Normal:** {0}
                **Current Time Format o'clock:** {1}

                **Command usage:** `{2}time format <normal|oclock> <text>`
                **Common Formats**:
                    %H 	Hour (24-hour clock) as a decimal number (00,23).
                    %I 	Hour (12-hour clock) as a decimal number (01,12).
                    %M 	Minute as a decimal number (00,59).
                    %p 	Locale’s equivalent of either AM or PM.
                More format available in [here](https://docs.python.org/3.7/library/time.html#time.strftime).
                '''.format(settings.timeFormatNormal, settings.timeFormatoClock, config.commandPrefix)
            if len(cmd1) == 1:
                embed = discord.Embed(
                    title=None, description=textInvalid, color=7388159)
                await ctx.send("Invalid Command", embed=embed)
                return
            else:
                if cmd1[1] == "normal":
                    if len(cmd1) == 2:
                        embed = discord.Embed(
                            title=None, description=textInvalid, color=7388159)
                        await ctx.send("Invalid Command", embed=embed)
                        return
                    else:
                        try:
                            testText = datetime.now().strftime(cmd1[2])
                        except ValueError as e1:
                            text = "**Error when previewing time:** \n{0}".format(str(e1.args))
                            embed = discord.Embed(title=None, description=text, color=7388159)
                            await ctx.send("Setting Failed", embed=embed)
                        else:
                            data.setData(str(ctx.guild.id), timeFormatNormal=cmd1[2])
                            text = "**New Time Format Normal:** {0}\n**Preview**: {1}".format(
                                data.getData(str(ctx.guild.id)).timeFormatNormal, testText)
                            embed = discord.Embed(
                                title=None, description=text, color=7388159)
                            await ctx.send("Setting Saved", embed=embed)

                        pass
                elif cmd1[1] == "oclock":
                    if len(cmd1) == 2:
                        embed = discord.Embed(
                            title=None, description=textInvalid, color=7388159)
                        await ctx.send("Invalid Command", embed=embed)
                        return
                    else:
                        try:
                            testText = datetime.now().strftime(cmd1[2])
                        except ValueError as e1:
                            text = "**Error when previewing time:** \n{0}".format(str(e1.args))
                            embed = discord.Embed(title=None, description=text, color=7388159)
                            await ctx.send("Setting Failed", embed=embed)
                        else:
                            data.setData(str(ctx.guild.id), timeFormatoClock=cmd1[2])
                            text = "**New Time Format o'clock:** {0}\n**Preview**: {1}".format(
                                data.getData(str(ctx.guild.id)).timeFormatoClock, testText)
                            embed = discord.Embed(
                                title=None, description=text, color=7388159)
                            await ctx.send("Setting Saved", embed=embed)
                else:
                    embed = discord.Embed(
                        title=None, description=textInvalid, color=7388159)
                    await ctx.send("Invalid Command", embed=embed)
                    return

        elif cmd[0] == "lang":
            settings = data.getData(str(ctx.guild.id))
            if len(cmd) == 1:
                text = '''**Current Announce TTS Language:** {0}

                **Command usage:** `{1}time lang <lang>`
                '''.format(settings.ttsLang, config.commandPrefix)
                embed = discord.Embed(title=None, description=text, color=7388159)
                await ctx.send("Invalid Command", embed=embed)
                return
            else:
                data.setData(str(ctx.guild.id), ttsLang=cmd[1])
                text = "**New Announce TTS Language:** {0}".format(
                    data.getData(str(ctx.guild.id)).ttsLang)
                embed = discord.Embed(title=None, description=text, color=7388159)
                await ctx.send("Setting Saved", embed=embed)
        elif cmd[0] == "hourly":
            settings = data.getData(str(ctx.guild.id))
            if len(cmd) == 1:
                data.setData(str(ctx.guild.id), timeHourly=not settings.timeHourly)
                text = "**New Announce Hourly:** {0}".format(
                    data.getData(str(ctx.guild.id)).timeHourly)
                embed = discord.Embed(title=None, description=text, color=7388159)
                await ctx.send("Setting Saved", embed=embed)
            else:
                if cmd[1].lower() == "true":
                    data.setData(str(ctx.guild.id), timeHourly=True)
                    text = "**New Announce Hourly:** {0}".format(
                        data.getData(str(ctx.guild.id)).timeHourly)
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Setting Saved", embed=embed)
                elif cmd[1].lower() == "false":
                    data.setData(str(ctx.guild.id), timeHourly=False)
                    text = "**New Announce Hourly:** {0}".format(
                        data.getData(str(ctx.guild.id)).timeHourly)
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Setting Saved", embed=embed)
                else:
                    text = '''**Current Announce Hourly:** {0}

                    **Command usage:** `{1}time hourly [True/False]`
                    '''.format(str(settings.timeHourly), config.commandPrefix)
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Invalid Command", embed=embed)
        elif cmd[0] == "hourlyPrefix":
            settings = data.getData(str(ctx.guild.id))
            if len(cmd) == 1:
                text = '''**Current Hourly Prefix Sound:** {0}

                **Command usage:** `{1}time hourlyPrefix <sound\remove>`
                Sounds is command name without `{1}`, use `{1}help` to get sound list.
                `{1}hourlyPrefix remove` to remove prefix sound.
                '''.format(settings.timeHourlyPrefixSound, config.commandPrefix)
                embed = discord.Embed(
                    title=None, description=text, color=7388159)
                await ctx.send("Invalid Command", embed=embed)
                return
            else:
                if cmd[1] == "remove":
                    data.setData(str(ctx.guild.id),timeHourlyPrefixSound="")
                    text = "**Hourly Prefix Sound Removed**"
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Setting Saved", embed=embed)
                elif cmd[1] not in soundData.getSoundCommandList():
                    text = "Sound {0} not found.".format(cmd[1])
                    embed = discord.Embed(title=None, description=text, color=7388159)
                    await ctx.send("Setting Failed", embed=embed)
                else:
                    data.setData(str(ctx.guild.id), timeHourlyPrefixSound=cmd[1])
                    text = "**New Hourly Prefix Sound:** {0}".format(
                        data.getData(str(ctx.guild.id)).timeHourlyPrefixSound)
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Setting Saved", embed=embed)
        elif cmd[0] == "hourlySuffix":
            settings = data.getData(str(ctx.guild.id))
            if len(cmd) == 1:
                text = '''**Current Hourly Suffix Sound:** {0}

                **Command usage:** `{1}time hourlySuffix <sound|remove>`
                Sounds is command name without `{1}`, use `{1}help` to get sound list.
                `{1}hourlySuffix remove` to remove Suffix sound.
                '''.format(settings.timeHourlySuffixSound, config.commandPrefix)
                embed = discord.Embed(
                    title=None, description=text, color=7388159)
                await ctx.send("Invalid Command", embed=embed)
                return
            else:
                if cmd[1] == "remove":
                    data.setData(str(ctx.guild.id), timeHourlySuffixSound="")
                    text = "**Hourly Suffix Sound Removed**"
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Setting Saved", embed=embed)
                elif cmd[1] not in soundData.getSoundCommandList():
                    text = "Sound {0} not found.".format(cmd[1])
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Setting Failed", embed=embed)
                else:
                    data.setData(str(ctx.guild.id),
                                 timeHourlySuffixSound=cmd[1])
                    text = "**New Hourly Suffix Sound:** {0}".format(
                        data.getData(str(ctx.guild.id)).timeHourlySuffixSound)
                    embed = discord.Embed(
                        title=None, description=text, color=7388159)
                    await ctx.send("Setting Saved", embed=embed)
            return
        else:
            await ctx.send("Unknown command. Try {0}time help.".format(config.commandPrefix))
            return
    else:
        await timeAnnounce.announce(str(ctx.guild.id), str(ctx.channel.id))
    return

async def on_message(message: discord.Message):
    dislog = ""
    try:
        dislog += "{0}@{1} in {2}({3}): {4}".format(message.author.display_name, message.author.name, message.channel.name, str(message.channel.id), message.content)
    except AttributeError:
        dislog += "{0}@{1}: {3}".format(message.author.display_name, message.author.name, message.content)
    if len(message.attachments) != 0:
        dislog += "\nAttachments: \n"
        for i in message.attachments:
            dislog +=  "{0}\n".format(i.url)
    logger.info(dislog)
    if (message.author.id == discord_client.user.id):
        return
    #SoundCommand
    server = message.guild
    channel = message.channel
    if server == None:
        await channel.send('This bot is not avaliable for private chat.')
        return
    voice = server.voice_client
    for i in soundData.getSoundCommandList():
        if message.content.startswith(config.commandPrefix + i):
            if voice == None:
                await channel.send("I'm not in a voice channel, use {0}join to let me in.".format(config.commandPrefix))
            else:
                if voice.is_playing():
                    await channel.send("Nope")
                    return
                voice.play(discord.FFmpegPCMAudio(soundData.getAssetFromCommand(i)))
            return
    for i in soundData.getSoundKeyWordList():
        if message.content.lower().find(i) != -1:
            if voice != None:
                if voice.is_playing():
                    return
                voice.play(discord.FFmpegPCMAudio(soundData.getAssetFromKeyWord(i)))
            return
    clockEmojis = "⏰ 🕰 🕐 🕑 🕒 🕓 🕔 🕕 🕖 🕗 🕘 🕙 🕚 🕛 🕜 🕝 🕟 🕞 🕠 🕡 🕢 🕣 🕤 🕥 🕦 🕧".split(" ")
    for i in clockEmojis:
        if message.content.find(i) != -1:
            await timeAnnounce.announce(str(message.guild.id), str(message.channel.id))

discord_client.add_listener(on_message, 'on_message')

if len(sys.argv) != 1:
    if sys.argv[1] == 'test':
        logger.info('There is no santax error,exiting...')
        exit()
    else:
        raise SyntaxError("Invaild command santax: {0}".format(sys.argv[1]))

logger.info("Bot has started")
logger.info("Listening ...")

discord_client.run(config.TOKEN)
