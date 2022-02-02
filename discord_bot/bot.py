import os
import discord
from discord.ext import commands

import export
from discord_bot.aux_functions import send_embed_decision, dm_register, get_letters_semester, get_letters_category, \
    get_student_file_page, letters_parse_args
from website_interact.html_analysis import extract_decisions, extract_letters_semester
from confidential import BOT_TOKEN
from users import User, UserNotFoundError, CacheError

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
async def get_decision(ctx, semester: str = 'last') -> None:
    semester = semester.replace(' ', '')
    bot_user = User(ctx.author.id)
    page = await get_student_file_page(ctx, bot_user)
    decisions = extract_decisions(page)
    await send_embed_decision(ctx, decisions, semester)


@bot.command()
async def get_letters(ctx, *args):
    first_arg, semesters, categories = letters_parse_args(args)
    if first_arg in categories or first_arg == 'all_cat':
        await get_letters_category(ctx, semesters, categories)
    else:
        await get_letters_semester(ctx, semesters, categories)


@bot.command()
async def register(ctx: discord.ext.commands.Context) -> None:
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


async def __is_lifetime_valid(ctx, lifetime):
    if lifetime <= 0:
        await ctx.send("Impossible de choisir une valeur négative")
        return False
    if lifetime > 10:
        await ctx.send("Vous n'avez pas le droit de mettre en cache un fichier pendant plus de 10 minutes")
        return False
    return True


@bot.command()
async def cache(ctx, lifetime = '5'):
    if not lifetime.isdigit():
        return
    lifetime = int(lifetime)
    if lifetime > 10:
        await ctx.send("Vous n'avez pas le droit de mettre en cache un fichier pendant plus de 10 minutes")
        return
    bot_user = User(ctx.author.id)
    page = await get_student_file_page(ctx, bot_user, check_cache=False)
    bot_user.cache(page, lifetime)
    await ctx.send(f'Dossier étudiant mis en cache pour une durée de {lifetime} minutes')


@bot.command()
async def set_cache_life(ctx, lifetime = '0'):
    if not lifetime.isdigit():
        return
    lifetime = int(lifetime)
    if not __is_lifetime_valid(ctx, lifetime):
        return
    bot_user = User(ctx.author.id)
    try:
        bot_user.set_cache_lifetime(lifetime)
        await ctx.send(f"Durée de maintien en cache modifiée. Nouvelle durée : {lifetime} minutes")
    except CacheError:
        await ctx.send("Vous n'avez pas de fichier en cache")


@bot.command()
async def del_cache(ctx):
    User(ctx.author.id).delete_cache()
    await ctx.send("Fichiers en cache supprimés")


@bot.command(name='export')
async def __export(ctx, file_format = "", *args):
    if file_format not in ('xls', 'json', 'latex', 'tex', 'html'):
        await ctx.send("Vous devez spécifier un format de fichier.\n"
                       "Formats disponibles : xls, json, latex, html")
        return
    bot_user = User(ctx.author.id)
    _, semesters, categories = letters_parse_args(args)
    page = await get_student_file_page(ctx, bot_user)
    ues = extract_letters_semester(page, semesters, categories)
    export_method = getattr(export, f"to_{file_format}")  # functions are named to_xls, to_json...
    export_file = export_method(ues)
    await ctx.send(file=discord.File(export_file))
    os.remove(export_file)
