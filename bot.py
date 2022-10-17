from apiclient.discovery import build
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import html
import os
import time
import yt_dlp as youtube_dl
import logging

logging.basicConfig(level=logging.INFO)

load_dotenv()

API_KEY = os.getenv('api_key')
DISCORD_TOKEN = os.getenv('discord_token')

vc = None
nowp = None
loops = False
loopp = False
song_queue = []

activity = discord.Activity(type=discord.ActivityType.watching, name="FredBoat SAMPAH")
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
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'options' : '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

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

def next_song(e):
    global nowp, loops, loopp
    
    if loops == True:
        # vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=nowp['filename']), after=next_song)
        vc.play(discord.FFmpegOpusAudio(executable="ffmpeg.exe", source=nowp['filename']), after=next_song)
    else:
        if len(song_queue) > 0:
            time.sleep(3)
            src = song_queue.pop(0)
            nowp = {
                'title': src['title'],
                'filename': src['filename'],
                'thumbnail': src['thumbnail'],
                'author': src['author']
            }
            # vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=src['filename']), after=next_song)
            vc.play(discord.FFmpegOpusAudio(executable="ffmpeg.exe", source=src['filename']), after=next_song)

# @bot.command(name='join', help='Supaya bot join ke voice channel')
@bot.slash_command(name='join', help='Supaya bot join ke voice channel')
async def join(ctx):

    if not ctx.author.voice:
        await ctx.respond("{} is not connected to a voice channel ❌.".format(ctx.author.name))
        return
    else:
        channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
    await ctx.respond("Joined voice channel {}".format(ctx.author.voice.channel.name))

# @bot.command(name='leave', help='Supaya bot keluar dari voice channel')
@bot.slash_command(name='leave', help='Supaya bot keluar dari voice channel')
async def leave(ctx):
    voice_client = ctx.guild.voice_client
    if voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send("Bot is not connected to a voice channel ❌.")

# @bot.command(name='np', help='Sekarang lagu apa')
@bot.slash_command(name='np', help='Sekarang lagu apa')
async def nowPlaying(ctx):
    global vc, nowp
    if vc.is_playing():
        embed = discord.Embed(title="Now Playing:",description=nowp['title'],color=discord.Color(0xA62019))
        embed.set_thumbnail(url=nowp['thumbnail'])
        footer_msg = "Added by "+nowp['author']
        embed.set_footer(text=footer_msg)
        await ctx.send(embed=embed)
    else:
        await ctx.send('Bot is not playing anything ❌.')

# @bot.command(name='queue', pass_context=True)
@bot.slash_command(name='nowplaying', pass_context=True)

async def npalt(ctx):
    await nowPlaying.invoke(ctx)

# @bot.command(name='q', help='menampilkan song_queue')
@bot.slash_command(name='q', help='menampilkan song_queue')
async def q(ctx):
    global song_queue

    if len(song_queue) > 0:
        msg = ''
        co = 1
        embed = discord.Embed(title="Queue", description=msg, color=discord.Color(0xA62019))

        for q in song_queue:
            name = str(co)+'. '+q['title']
            value ='Added by '+q['author']
            embed.add_field(name=name,value=value, inline=False)
            co += 1

        await ctx.send(embed=embed)
    else:
        await ctx.send('There is no queue at the moment ❌.')

# @bot.command(name='queue', pass_context=True)
@bot.slash_command(name='queue', pass_context=True)

async def qalt(ctx):
    await q.invoke(ctx)

# @bot.command(name='search', help='Cari lagu terus pilih')
@bot.slash_command(name='search', help='Cari lagu terus pilih')
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
            'video_id': item['id']['videoId'],
            'thumbnail': item['snippet']['thumbnails']['default']['url']
        }
        tmp_arr.append(qData)
        msg += str(co) + '. ' + qData['title'] + '\n\n'
        co += 1
    embed = discord.Embed(title="Showing 10 queries for '`"+content+"`' based on Youtube:", description=msg, color=discord.Color(0xA62019))
    choice = await ctx.send(embed=embed)
    msg = await bot.wait_for('message', check=lambda message: message.author == ctx.author)

    await choice.delete()

    if msg.content == 'cancel' or msg.content == 'Cancel':
        return
    
    selected = tmp_arr[int(msg.content)-1]

    if not ctx.author.voice:
        await ctx.send("{} is not connected to a voice channel ❌.".format(ctx.author.name))
        return
    else:
        voice_client = ctx.guild.voice_client
        if(voice_client == None):
                channel = ctx.author.voice.channel
                await channel.connect()
                await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
        server = ctx.guild

    voice_client = ctx.guild.voice_client

    if voice_client.is_playing():
        url = 'www.youtube.com/watch?v='+selected['video_id']
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        qData = {
            'title': selected['title'],
            'filename': filename,
            'thumbnail': selected['thumbnail'],
            'author': ctx.author.name
        }
        song_queue.append(qData)
        await ctx.send('**Added to queue:** {}'.format(selected['title'])) 
    else:
        server = ctx.guild
        vc = server.voice_client
        async with ctx.typing():
            url = 'www.youtube.com/watch?v='+selected['video_id']
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            nowp = {
                'title': selected['title'],
                'filename': filename,
                'thumbnail': selected['thumbnail'],
                'author': ctx.author.name
            }
            # vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=next_song)
            vc.play(discord.FFmpegOpusAudio(executable="ffmpeg.exe", source=filename), after=next_song)
        embed = discord.Embed(title="Now Playing:",description=selected['title'], color=discord.Color(0xA62019))
        embed.set_thumbnail(url=nowp['thumbnail'])
        footer_msg = "Requested by "+ctx.author.name
        embed.set_footer(text=footer_msg)
        await ctx.send(embed=embed)

# @bot.command(name='play', help='Muter lagu')
@bot.slash_command(name='play', help='Muter lagu')
async def play(ctx,*,content):

    global vc, nowp, song_queue

    if not ctx.author.voice:
        await ctx.send("{} is not connected to a voice channel ❌.".format(ctx.author.name))
        return
    else:
        voice_client = ctx.guild.voice_client
        if(voice_client == None):
                channel = ctx.author.voice.channel
                await channel.connect()
                await ctx.guild.change_voice_state(channel=channel, self_deaf=True)
        server = ctx.guild

    voice_client = ctx.guild.voice_client

    request = youtube.search().list(q=content,part='snippet',type='video',maxResults=1)
    res = request.execute()
    data = {
        'title': html.unescape(res['items'][0]['snippet']['title']),
        'video_id': res['items'][0]['id']['videoId'],
        'thumbnail': res['items'][0]['snippet']['thumbnails']['default']['url']
    }
    url = 'www.youtube.com/watch?v='+data['video_id']

    if voice_client.is_playing():
        filename = await YTDLSource.from_url(url, loop=bot.loop)
        qData = {
            'title': data['title'],
            'filename': filename,
            'thumbnail': data['thumbnail'],
            'author': ctx.author.name
        }
        song_queue.append(qData)
        await ctx.send('**Added to queue:** {}'.format(data['title'])) 
    else:
        server = ctx.guild
        vc = server.voice_client
        async with ctx.typing():
            filename = await YTDLSource.from_url(url, loop=bot.loop)
            nowp = {
                'title': data['title'],
                'filename': filename,
                'thumbnail': data['thumbnail'],
                'author': ctx.author.name
            }
            # vc.play(discord.FFmpegPCMAudio(executable="ffmpeg.exe", source=filename), after=next_song)
            vc.play(discord.FFmpegOpusAudio(executable="ffmpeg.exe", source=filename), after=next_song)
        embed = discord.Embed(title="Now Playing:",description=data['title'], color=discord.Color(0xA62019))
        embed.set_thumbnail(url=data['thumbnail'])
        embed_msg = "Requested by "+ctx.author.name
        embed.set_footer(text=embed_msg)
        await ctx.send(embed=embed)

# @bot.command(name='pause', help='Berhenti sementara')
@bot.slash_command(name='pause', help='Berhenti sementara')
async def pause(ctx):
    global vc
    if vc.is_playing():
        vc.pause()
    else:
        if vc.is_paused():
            await ctx.respond("Bot was paused.")
        else:
            await ctx.respond("Bot is not playing anything ❌.")

# @bot.command(name='resume', help='Melanjutkan putar')
@bot.slash_command(name='resume', help='Melanjutkan putar')
async def resume(ctx):
    global vc
    if vc.is_paused():
        vc.resume()
    else:
        if vc.is_playing():
            await ctx.respond("Bot is already playing.")
        else:
            await ctx.respond("Bot is not playing anything ❌.")

# @bot.command(name='skip', help='Lanjut lagu selanjutnya')
@bot.slash_command(name='skip', help='Lanjut lagu selanjutnya')
async def skip(ctx):
    global song_queue, vc, nowp, loops
    vc.stop()
    if loops == True:
        next_song
    else:
        if len(song_queue) > 0:
            time.sleep(3)
            src = song_queue[0]
            embed = discord.Embed(title="Now Playing:",description=src['title'], color=discord.Color(0xA62019))
            embed.set_thumbnail(url=src['thumbnail'])
            embed_msg="Added by "+src['author']
            embed.set_footer(text=embed_msg)
            next_song
            await ctx.send(embed=embed)
    await ctx.respond("_Skipped!_")

# @bot.command(name='remove', help='Hapus dari daftar urutan, gunakan command !q / !queue untuk melihat urutan')
@bot.slash_command(name='remove', help='Hapus dari daftar urutan, gunakan command !q / !queue untuk melihat urutan')
async def remove(ctx, index):
    global song_queue
    removed = song_queue.pop(index-1)
    await ctx.send(removed['title'] + ' removed from queue.')

# @bot.command(name='stop', help='Menghentikan lagu')
@bot.slash_command(name='stop', help='Menghentikan lagu')
async def stop(ctx):

    global vc

    if vc.is_playing():
        vc.stop()
        await ctx.send("Bot stopped.")
    else:
        await ctx.send("Bot is not playing anything at the moment ❌.")

# @bot.command(name='clear', help='Clear queue')
@bot.slash_command(name='clear', help='Clear queue')
async def clear(ctx):
    global queue
    song_queue.clear()
    await ctx.send("Queue cleared")

# @bot.command(name='loops', help='Turned on song loop')
@bot.slash_command(name='loops', help='Turned on song loop')
async def loop_song(ctx):
    global loops, nowp
    if loops == True:
        loops = False
        await ctx.send("Song loop turned off")
    else:
        loops = True
        await ctx.send("Song loop turned on, "+nowp['title']+" will be looped")

# @bot.command(name='loopp', help='Turned on playlist loop')
@bot.slash_command(name='loopp', help='Turned on playlist loop')
async def loop_playlist(ctx):
    global loopp, nowp
    if loopp == True:
        loopp = False
        await ctx.send("Playlist Loop turned off")
    else:
        loopp = True
        await ctx.send("Playlist Loop turned on")

if __name__ == "__main__" :
    bot.run(DISCORD_TOKEN)