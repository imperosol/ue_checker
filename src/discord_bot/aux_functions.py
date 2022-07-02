import asyncio
import concurrent.futures
import typing
from typing import Callable

import discord
import requests

from src.website_interact.html_analysis import get_ue_td_html
from src.discord_bot import commands as bot
from src.users import UserNotFoundError, User
from src.website_interact.ent_requests import get_student_file
from src.website_interact.html_analysis import extract_letters_semester, extract_letters_category
from src.custom_types import ue_set, ue_t


async def send_embed_letters(ctx, letters: ue_set) -> None:
    embed = discord.Embed(title="Résultats UE")
    for field in letters:
        result = ""
        for subfield in letters[field]:
            ue_list = letters[field][subfield]
            for ue in ue_list:
                if len(ue) > 0:
                    result += f"- {ue[0]}" \
                              + (f" : {ue[1]}" if len(ue) >= 2 else "") \
                              + (f"({ue[2]} crédits)" if len(ue) >= 3 else "") \
                              + f" [{subfield}]\n"
        if result:
            embed.add_field(name=field, value=result, inline=True)
    await ctx.send(embed=embed)


async def send_embed_decision(ctx, decisions: dict[str, str], semester) -> None:
    embed = discord.Embed(title="Décisions jurys")
    if semester == 'all':
        for decision in decisions:
            if decisions[decision]:
                embed.add_field(name=decision, value=decisions[decision], inline=True)
    elif semester == 'last':
        key = next((key for key in reversed(decisions.keys()) if decisions[key] != ''), None)
        if key:
            embed.add_field(name=key, value=decisions[key], inline=True)
        else:
            embed.add_field(name="", value="Pas d'avis de jury trouvé", inline=True)
    elif semester not in decisions:
        await ctx.send("Semestre non trouvé")
        return
    elif decisions[semester] != "":
        embed.add_field(name=semester, value=decisions[semester], inline=True)
    else:
        embed.add_field(name=semester, value="Pas d'avis publié pour le moment", inline=True)
    await ctx.send(embed=embed)


async def __init_session_from_discord(ctx, bot_user: User, session: requests.Session) -> None:
    """
    initialize the ent session of a user.
    Work pretty like the init_session() method of the User class, but provide discord messages
    throughout the process to inform the user who made the command of the key steps leading to the final result

    :param ctx: the context of the command
    :param bot_user: the user who made the command. Must not be confused with a discord user. It must be an instance
    of the custom User class of this project.
    :param session: the ent session to initialize ; should ideally be wrap into a context manager using the with keyword
    :raise UserNotFoundError: when the bot_user is not found in the database
    (probably because he didn't register himself)
    """
    loop = asyncio.get_running_loop()
    try:
        await asyncio.gather(
            ctx.send("Connexion au serveur"),
            loop.run_in_executor(None, bot_user.init_session, session)
        )
    except UserNotFoundError:
        await ctx.send("Connexion impossible : utilisateur inexistant dans la base de données\n"
                       "Enregistrez-vous d'abord avec la commande `!ent_register`")
        raise UserNotFoundError()


async def __get_student_file_from_discord(ctx, session: requests.Session) -> requests.Response:
    loop = asyncio.get_running_loop()
    trash_value, page = await asyncio.gather(
        ctx.send("Accès au dossier étudiant"),
        loop.run_in_executor(None, get_student_file, session)
    )
    return page


async def get_student_file_page(ctx, bot_user: User, check_cache = True):
    if check_cache:
        page = bot_user.get_cache()
        if page is not None:
            return page
    with requests.Session() as session:
        try:
            await __init_session_from_discord(ctx, bot_user, session)
        except UserNotFoundError:
            return
        nb_try = 4
        while nb_try > 0:
            try:
                page = await __get_student_file_from_discord(ctx, session)
                page = get_ue_td_html(page)
                nb_try = 0
            except:
                nb_try -= 1
                await ctx.send("Erreur lors de la récupération de la page, rechargement en cours...")
        return page


async def __dm_get_confidential_datas(ctx: discord.DMChannel, user: discord.User) -> tuple[str, str]:
    def check(m):
        return isinstance(m.channel, discord.DMChannel) and m.author == user

    while True:
        await ctx.send("Donnez votre identifiant sur l'ENT.")
        username = await bot.bot.wait_for('message', check=check)
        username = username.content
        await ctx.send("Donnez votre mot de passe.")
        password = await bot.bot.wait_for('message', check=check)
        password = password.content
        await ctx.send("Confirmez-vous vos données d'authentification ? (o/n)")
        answer = await bot.bot.wait_for('message', check=check)
        if answer.content.lower() in 'ouiyes':
            return username, password


async def dm_register(user: discord.User) -> User | None:
    ctx = user.dm_channel
    await ctx.send("Vous avez demandé à vous enregistrer. Vos informations personnelles seront stockées sur une base "
                   "de données. Votre mot de passe sera crypté avec une clef accessible uniquement par Thomas  Girod, "
                   "le développeur de ce bot. Ne continuez que si vous lui faites confiance.\n\n Voulez-vous "
                   "poursuivre ? o/n")
    answer: discord.Message = await bot.bot.wait_for('message',
                                                     check=lambda m: isinstance(m.channel, discord.DMChannel))
    if answer.content.lower() not in 'ouiyes':  # user can answer 'o', 'oui', 'y' or 'yes'
        await ctx.send("Abandon de l'opération")
        return None
    username, password = await __dm_get_confidential_datas(ctx, user)
    return User(user.id, username, password)


async def __get_letters(ctx, extract_callback: Callable, semester: list | tuple = None, categories = None) -> None:
    bot_user = User(ctx.author.id)
    page = await get_student_file_page(ctx, bot_user)
    letters = extract_callback(page, semester, categories)
    await send_embed_letters(ctx, letters)


async def get_letters_semester(ctx, semester = None, categories = None) -> None:
    await __get_letters(ctx, extract_letters_semester, semester, categories)


async def get_letters_category(ctx, semester = None, categories = None) -> None:
    await __get_letters(ctx, extract_letters_category, semester, categories)


def __parse_categories(args: tuple) -> tuple:
    categories = set(arg for arg in args if arg in ('CS', 'TM', 'ME', 'EC', 'CT', 'HT', 'ST', 'HP'))
    if len(categories) == 0 or 'ALL_CAT' in args:
        categories = ('CS', 'TM', 'ME', 'EC', 'CT', 'ST', 'HP')
    elif 'HT' in categories:  # ues HT are named CT in the ENT
        categories.remove('HT')
        categories.add('CT')
    return tuple(categories)


def __parse_semesters(args: tuple) -> tuple:
    if 'ALL_SEM' in args:
        return 'all_sem',
    branches = ('TC', 'ISI', 'RT', 'MTE', 'MM', 'GM', 'GI', 'A2I')
    return tuple(set(arg for arg in args if any(arg.startswith(branch) for branch in branches)))


def letters_parse_args(args: tuple | list) -> tuple[str | None, tuple | None, tuple]:
    if len(args) == 0:  # default behaviour when no argument : all letters of last semester
        return None, None, ('CS', 'TM', 'ME', 'EC', 'CT', 'ST', 'HP')
    first_arg = args[0]
    if first_arg.startswith('all'):
        first_arg = first_arg.lower()
    args = tuple(set(arg.upper() for arg in args))  # remove eventual duplicates and upper everything
    categories = __parse_categories(args)
    semesters = __parse_semesters(args)
    return first_arg, semesters, categories


def get_ues_to_watch(user: User) -> list[str]:
    result = []
    with requests.Session() as session:
        user.init_session(session)
        page = get_student_file(session)
        ues = extract_letters_semester(page)
        for category in list(ues.values())[0].values():
            if len(category) > 0:
                result += [ue for ue in category if len(ue) == 1]
    return result


def get_ues_changes(user: User, old_ues: list[str]) -> list[ue_t]:
    new_ues = []
    with requests.Session() as session:
        user.init_session(session)
        page = get_student_file(session)
        ues = extract_letters_semester(page)
        for category in list(ues.values())[0].values():
            if len(category) > 0:
                new_ues += [ue for ue in category if len(ue) > 1 and ue[0] in old_ues]
    return new_ues


