import asyncio
import discord
from discord.ext import commands,tasks
import os
from dotenv import load_dotenv
import youtube_dl
from apiclient.discovery import build
import html

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

query = []
songs = asyncio.Queue()
play_next_song = asyncio.Event()

async def audio_player_task():
    while True:
        play_next_song.clear()
        current = await songs.get()
        current.start()
        await play_next_song.wait()

# def toggle_next():
#     bot.loop.call_soon_threadsafe(play_next_song.get)

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

@bot.command(name='search', help='Cari lagu terus pilih')
async def search(ctx, *, content):
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
        print(qData)
        tmp_arr.append(qData)
        msg += str(co) + '. ' + qData['title'] + '\n\n'
        co += 1
    await ctx.send(msg)
    msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)
    # print(msg.content)
    # print(tmp_arr[int(msg.content)-1]['title'])
    selected = tmp_arr[int(msg.content)-1]

    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        channel = ctx.message.author.voice.channel
        try :
            await channel.connect()
            
        except:
            server = ctx.message.guild
            voice_channel = server.voice_client

    voice_client = ctx.message.guild.voice_client

    if voice_client.is_playing():
        url = 'www.youtube.com/watch?v='+selected['video_id']
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        await songs.put(filename)
    else:
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            url = 'www.youtube.com/watch?v='+selected['video_id']
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            await songs.put(voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename)))
        await ctx.send('**Now playing:** {}'.format(selected['title']))
    

@bot.command(name='play', help='Muter lagu')
async def play(ctx,url):
    try:
        server = ctx.message.guild
        voice_channel = server.voice_client

        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            voice_channel.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename))
        await ctx.send('**Now playing:** {}'.format(filename))
    except:
        await ctx.send("Bot is not connected to a voice channel")

@bot.command(name='pause', help='Berhenti sementara')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_paused():
        await voice_client.resume()
    else:
        await ctx.send("Bot was not playing anything before this. Use play command")

@bot.command(name='stop', help='Menghentikan lagu')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_playing():
        await voice_client.stop()
    else:
        await ctx.send("Bot is not playing anything at the moment.")

if __name__ == "__main__" :
    bot.loop.create_task(audio_player_task())
    bot.run(DISCORD_TOKEN)