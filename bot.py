"""
Bot de Discord que toca um áudio automaticamente quando alguém
entra em QUALQUER canal de voz do servidor.

REQUISITOS:
    pip install discord.py[voice] python-dotenv
    Instalar o FFmpeg e deixá-lo no PATH do sistema:
    - Windows: https://www.gyan.dev/ffmpeg/builds/ (baixe o "release full",
      extraia e adicione a pasta "bin" nas variáveis de ambiente PATH)
    - Mac: brew install ffmpeg
    - Linux: sudo apt install ffmpeg

COMO USAR:
    1. Coloque o arquivo de áudio (mp3 ou wav) na mesma pasta deste script
       e ajuste o nome em AUDIO_FILE abaixo.
    2. Crie um arquivo ".env" na mesma pasta com o conteúdo:
           DISCORD_TOKEN=seu_token_aqui
    3. No Developer Portal (discord.com/developers/applications), na aba
       "Bot", ative os intents: SERVER MEMBERS INTENT e PRESENCE INTENT
       (opcional) e principalmente VOICE STATE (já vem via intents.voice_states).
    4. Rode: python bot.py
"""

import os
import asyncio
import discord
import imageio_ffmpeg
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Nome do arquivo de áudio que será tocado (coloque-o na mesma pasta)
AUDIO_FILE = "audio.mp3"

# Caminho do ffmpeg embutido (não depende de instalação no sistema/servidor)
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

intents = discord.Intents.default()
intents.voice_states = True  # necessário para detectar entrada em call
intents.members = True       # necessário para saber quem entrou

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")


@bot.event
async def on_voice_state_update(member, before, after):
    print(f"[DEBUG] Evento detectado: {member} | antes={before.channel} | depois={after.channel}")

    # Ignora o próprio bot
    if member.bot:
        return

    # Detecta quando alguém ENTROU em um canal de voz
    # (before.channel é None ou diferente do after.channel quando entra)
    entrou_em_canal = after.channel is not None and before.channel != after.channel

    if not entrou_em_canal:
        print("[DEBUG] Não foi uma entrada em canal, ignorando.")
        return

    canal_de_voz = after.channel
    print(f"[DEBUG] Tentando entrar no canal: {canal_de_voz}")

    try:
        # Conecta no canal onde a pessoa entrou
        voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)

        if voice_client and voice_client.is_connected():
            if voice_client.channel != canal_de_voz:
                await voice_client.move_to(canal_de_voz)
        else:
            voice_client = await canal_de_voz.connect()

        # Toca o áudio
        if not voice_client.is_playing():
            source = discord.FFmpegPCMAudio(AUDIO_FILE, executable=FFMPEG_PATH)
            voice_client.play(source)

            # Espera o áudio terminar de tocar
            while voice_client.is_playing():
                await asyncio.sleep(0.5)

        # Sai do canal depois de tocar
        await voice_client.disconnect()

    except Exception as e:
        print(f"Erro ao tocar áudio: {e}")


bot.run(TOKEN)
