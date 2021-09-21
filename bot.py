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

activity = discord.Activity(type=discord.ActivityType.watching, name="Indahnya negeriku Indonesia")

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents, activity=activity, status=discord.Status.idle)
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
song_queue = []

def tes(e):
    if len(song_queue) > 0:
        time.sleep(3)
        src = song_queue.pop(0)
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=src['filename']), after=tes)

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

@bot.command(name='q', help='menampilkan song_queue')
async def q(ctx):
    global song_queue

    if len(song_queue) > 0:
        msg = '**Queue**: \n'
        co = 1
        for q in song_queue:
            msg += str(co) + '. ' + q['title'] + '\n'
            co += 1
        await ctx.send(msg)
    else:
        await ctx.send('There is no queue at the moment.')

@bot.command(name='queue', pass_context=True)
async def qalt(ctx):
    await q.invoke(ctx)

@bot.command(name='np', help='Sekarang lagu apa')
async def nowPlaying(ctx):
    global vc, nowp
    if vc.is_playing():
        await ctx.send('**Now playing:** {}'.format(nowp))
    else:
        await ctx.send('Bot is not playing anything.')

@bot.command(name='search', help='Cari lagu terus pilih')
async def search(ctx, *, content):

    global vc, nowp, song_queue

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
        #(voice_client.is_playing())
        url = 'www.youtube.com/watch?v='+selected['video_id']
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        qData = {
            'title': selected['title'],
            'filename': filename
        }
        song_queue.append(qData)
        await ctx.send('**Added to queue:** {}'.format(selected['title'])) 
    else:
        #print(voice_client.is_playing())
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

    global vc, nowp, song_queue

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
        #print(voice_client.is_playing())
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        qData = {
            'title': filename,
            'filename': filename
        }
        song_queue.append(qData)
        await ctx.send('**Added to queue:** {}'.format(filename)) 
    else:
        #print(voice_client.is_playing())
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
    if vc.is_playing():
        vc.pause()
    else:
        if vc.is_paused():
            await ctx.send("Bot was paused.")
        else:
            await ctx.send("Bot is not playing anything.")

@bot.command(name='resume', help='Melanjutkan putar')
async def resume(ctx):
    global vc
    if vc.is_paused():
        vc.resume()
    else:
        if vc.is_playing():
            await ctx.send("Bot was resumed.")
        else:
            await ctx.send("Bot is not playing anything.")

@bot.command(name='skip', help='Lanjut lagu selanjutnya')
async def skip(ctx):
    global song_queue, vc, nowp
    if len(song_queue) > 0:
        vc.stop()
        src = song_queue.pop(0)
        nowp = src['title']
        vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=src['filename']), after=tes)
        await ctx.send('**Now playing:** {}'.format(src['title'])) 
    else:
        await ctx.send('Queue empty.')

@bot.command(name='stop', help='Menghentikan lagu')
async def stop(ctx):

    global vc

    if vc.is_playing():
        vc.stop()
        await ctx.send("Bot stopped.")
    else:
        await ctx.send("Bot is not playing anything at the moment.")

if __name__ == "__main__" :
    bot.run(DISCORD_TOKEN)