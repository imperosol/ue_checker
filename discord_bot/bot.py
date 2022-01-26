import discord
import requests
import asyncio
from discord.ext import commands

from discord_bot.aux_functions import send_embed_letters, send_embed_decision, init_session_from_discord, \
    get_student_file_from_discord, dm_register
from website_interact.ent_requests import get_student_file
from website_interact.html_analysis import extract_letters, extract_decisions
from confidential import BOT_TOKEN
from users import User, UserNotFoundError

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!')


def start_bot():
    bot.run(BOT_TOKEN)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


@bot.command()
async def get_letters(ctx, semester: str = 'last'):
    semester = semester.replace(' ', '')
    bot_user = User(ctx.author.id)
    with requests.Session() as session:
        loop = asyncio.get_running_loop()
        try:
            await asyncio.gather(
                ctx.send("Connexion au serveur"),
                loop.run_in_executor(None, bot_user.init_session, session)
            )
        except UserNotFoundError:
            await ctx.send("Connexion impossible : utilisateur inexistant dans la base de données\n"
                           "Enregistrez-vous d'abord avec la commande `!ent_register`")
            return
        trash_value, page = await asyncio.gather(
            ctx.send("Accès au dossier étudiant"),
            loop.run_in_executor(None, get_student_file, session)
        )
        letters = extract_letters(page)
        await send_embed_letters(ctx, letters, semester)


@bot.command()
async def get_decision(ctx, semester: str = 'last') -> None:
    semester = semester.replace(' ', '')
    bot_user = User(ctx.author.id)
    with requests.Session() as session:
        loop = asyncio.get_running_loop()
        try:
            await init_session_from_discord(ctx, bot_user, session)
        except UserNotFoundError:
            return
        page = await get_student_file_from_discord(ctx, session)
        decisions = extract_decisions(page)
        await send_embed_decision(ctx, decisions, semester)

#
# async def notify_new_decision(ctx, decision):
#     await ctx.send(f"Nouvelle décision :\n{decision}")
#
#
# def watch(ctx, delay):
#     exit_flag = threading.Event()
#     with requests.Session() as session:
#         init_session(session)
#         page = get_student_file(session)
#         decisions = extract_decisions(page)
#         key = list(decisions.keys())[-1]
#         last_decision = decisions[key]
#         while True:
#             while not exit_flag.wait(delay):
#                 try:
#                     page = get_student_file(session)
#                     new_decision = extract_decisions(page)[key]
#                     print(new_decision)
#                     if last_decision != new_decision:
#                         last_decision = new_decision
#                     loop = asyncio.new_event_loop()
#                     asyncio.set_event_loop(loop)
#                     loop.run_until_complete(notify_new_decision(ctx, new_decision))
#                     loop.close()
#                 except InterruptedError:
#                     pass
#
#
# @bot.command()
# async def start_ue_watch(ctx, delay = 1):
#     delay = int(delay)
#     await ctx.send(f"Début de l'observation du dossier étudiant. Observation toutes les {delay} secondes")
#     t = threading.Thread(target=watch, args=(ctx, delay), daemon=True)
#     t.start()


@bot.command()
async def ent_register(ctx: discord.ext.commands.Context) -> None:
    new_user = User(ctx.author.id)
    if new_user.is_registered():
        await ctx.send(f"L'utilisateur {ctx.author.name} est déjà enregistré\n"
                       f"Vous pouvez vous désinscrire avec la commande `!unregister`")
        return
    if ctx.author.dm_channel is None:
        await ctx.author.create_dm()
    new_user = await dm_register(ctx.author)
    if new_user is not None:
        new_user.save()
        await ctx.author.dm_channel.send("Enregistrement confirmé. Vous pouvez vous désinscire à tout moment avec la "
                                         "commande `!unregister`")


@bot.command()
async def unregister(ctx):
    try:
        User(ctx.author.id).remove()
        await ctx.send("Utilisateur désinscrit")
    except UserNotFoundError:
        await ctx.send(f"L'utilisateur {ctx.author.name} n'est pas enregistré\n"
                       f"Vous pouvez vous inscrire avec la commande `!ent_register`")
