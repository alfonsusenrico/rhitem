from apiclient.discovery import build
import asyncio
import discord
from discord.ext import commands,tasks
from discord.utils import get
from dotenv import load_dotenv
import html
import os
import time
import youtube_dl

load_dotenv()

DISCORD_TOKEN = os.getenv('discord_token')
API_KEY = os.getenv('api_key')

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)
youtube = build('youtube','v3',developerKey = API_KEY)

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quite': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options' : '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

vc = None
nowp = None
query = []

def tes(e):
    print('song finished')
    print(vc)
    if len(query) > 0:
        time.sleep(3)
        src = query.pop[0]
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=src['filename']), after=tes)
        #await gCtx.send('**Now playing:** {}'.format(src['title'])) 

class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

@bot.command(name='join', help='Supaya bot join ke voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
    await channel.connect()

@bot.command(name='leave', help='Supaya bot keluar dari voice channel')
async def leave(ctx):
    voice_client = ctx.messsage.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("Bot is not connected to a voice channel.")

# @bot.command(name='tes', help='tes')
# async def test(ctx):
#     print(ctx.voice_client)
#     if(ctx.voice_client == None):
#         channel = ctx.message.author.voice.channel
#         await channel.connect()

@bot.command(name='q', help='menampilkan query')
async def q(ctx):
    global query
    msg = '**Current query**: \n'
    co = 1
    for q in query:
        msg += str(co) + '. ' + q['title'] + '\n'
    await ctx.send(msg)

@bot.command(pass_context=True)
async def queue(ctx):
    await q.invoke(ctx)

@bot.command(name='np', help='Sekarang lagu apa')
async def nowPlaying(ctx):
    global vc, nowp
    if vc.is_playing():
        await ctx.send('**Now playing:** {}'.format(nowp))
    else:
        await ctx.send('Bot is not playing anything')

@bot.command(name='search', help='Cari lagu terus pilih')
async def search(ctx, *, content):

    global vc, nowp, query

    request = youtube.search().list(q=content,part='snippet',type='video',maxResults=10)
    res = request.execute()
    msg = ''
    tmp_arr = []
    co = 1
    for item in res['items']:
        qData = {
            'title': html.unescape(item['snippet']['title']),
            'video_id': item['id']['videoId']
        }
        tmp_arr.append(qData)
        msg += str(co) + '. ' + qData['title'] + '\n\n'
        co += 1
    await ctx.send(msg)
    msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    selected = tmp_arr[int(msg.content)-1]

    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        voice_client = ctx.message.guild.voice_client
        if(voice_client == None):
                channel = ctx.message.author.voice.channel
                await channel.connect()
        server = ctx.message.guild

    voice_client = ctx.message.guild.voice_client

    if voice_client.is_playing():
        print(voice_client.is_playing())
        url = 'www.youtube.com/watch?v='+selected['video_id']
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        qData = {
            'title': selected['title'],
            'filename': filename
        }
        query.append(qData)
        await ctx.send('**Added to Queue:** {}'.format(selected['title'])) 
    else:
        print(voice_client.is_playing())
        server = ctx.message.guild
        vc = server.voice_client
        async with ctx.typing():
            url = 'www.youtube.com/watch?v='+selected['video_id']
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            nowp = selected['title']
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=tes)
        await ctx.send('**Now playing:** {}'.format(selected['title'])) 

@bot.command(name='play', help='Muter lagu')
async def play(ctx,url):

    global vc, nowp, query

    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        voice_client = ctx.message.guild.voice_client
        if(voice_client == None):
                channel = ctx.message.author.voice.channel
                await channel.connect()
        server = ctx.message.guild

    voice_client = ctx.message.guild.voice_client

    if voice_client.is_playing():
        print(voice_client.is_playing())
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        qData = {
            'title': filename,
            'filename': filename
        }
        query.append(qData)
        await ctx.send('**Added to Queue:** {}'.format(filename)) 
    else:
        print(voice_client.is_playing())
        server = ctx.message.guild
        vc = server.voice_client
        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            nowp = filename
            vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=tes)
        await ctx.send('**Now playing:** {}'.format(filename)) 

    # try:
    #     server = ctx.message.guild
    #     voice_channel = server.voice_client

    #     async with ctx.typing():
    #         filename = await YTDLSource.from_url(url, loop=bot.loop)
    #         voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
    #     await ctx.send('**Now playing:** {}'.format(filename))
    # except:
    #     await ctx.send("Bot is not connected to a voice channel")

@bot.command(name='pause', help='Berhenti sementara')
async def pause(ctx):
    global vc
    try:
        if vc.is_playing():
            await vc.pause()
        else:
            await ctx.send("Bot is not playing anything")
    except:
        await ctx.send("Bot is not connected to a voice channel")

@bot.command(name='resume', help='Melanjutkan putar')
async def resume(ctx):
    global vc
    try:
        if vc.is_paused():
            await vc.resume()
        else:
            await ctx.send("Bot is not playing anything")
    except:
        await ctx.send("Bot is not connected to a voice channel")

@bot.command(name='stop', help='Menghentikan lagu')
async def stop(ctx):

    global vc

    if vc.is_playing():
        await vc.stop()
    else:
        await ctx.send("Bot is not playing anything at the moment.")

if __name__ == "__main__" :
    bot.run(DISCORD_TOKEN)