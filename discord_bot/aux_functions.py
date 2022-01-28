import asyncio

import discord
import requests

from discord_bot import bot
from users import UserNotFoundError, User
from website_interact.ent_requests import get_student_file


async def send_embed_letters(ctx, letters: dict[str, dict[str, list[str, str, str]]]) -> None:
    embed = discord.Embed(title="Résultats UE")
    for field in letters:
        result = ""
        for subfield in letters[field]:
            ue_list = letters[field][subfield]
            for ue in ue_list:
                if len(ue) > 0:
                    result += f"- {ue[0]} : {ue[1]} " \
                              + (f"({ue[2]} crédits)" if len(ue) == 3 else "") \
                              + f" [{subfield}]\n"
        if result:
            embed.add_field(name=field, value=result, inline=True)
    await ctx.send(embed=embed)


async def send_embed_decision(ctx, decisions: dict[str, str], semester) -> None:
    embed = discord.Embed(title="Décisions jurys")
    if semester == 'all':
        for decision in decisions:
            embed.add_field(name=decision, value=decisions[decision], inline=True)
    elif semester == 'last':
        key = list(decisions.keys())[-1]
        embed.add_field(name=key, value=decisions[key], inline=True)
    elif semester not in decisions:
        await ctx.send("Semestre non trouvé")
        return
    else:
        embed.add_field(name=semester, value=decisions[semester], inline=True)
    await ctx.send(embed=embed)


async def init_session_from_discord(ctx, bot_user, session):
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


async def get_student_file_from_discord(ctx, session) -> requests.Response:
    loop = asyncio.get_running_loop()
    trash_value, page = await asyncio.gather(
        ctx.send("Accès au dossier étudiant"),
        loop.run_in_executor(None, get_student_file, session)
    )
    return page


async def dm_register(user: discord.User) -> User | None:
    ctx = user.dm_channel
    await ctx.send("Vous avez demandé à vous enregistrer. Vos informations personnelles seront stockées sur une base "
                   "de données. Votre mot de passe sera crypté avec une clef accessible uniquement par Thomas  Girod, "
                   "le développeur de ce bot. Ne continuez que si vous lui faites confiance.\n\n Voulez-vous "
                   "poursuivre ? o/n")
    answer: discord.Message = await bot.bot.wait_for('message', check=lambda m: isinstance(m.channel, discord.DMChannel))
    if answer.content.lower() not in 'ouiyes':  # user can answer 'o', 'oui', 'y' or 'yes'
        await ctx.send("Abandon de l'opération")
        return None
    while True:
        check = lambda m: isinstance(m.channel, discord.DMChannel) and m.author == user
        await ctx.send("Donnez votre identifiant sur l'ENT.")
        username = await bot.bot.wait_for('message', check=check)
        username = username.content
        await ctx.send("Donnez votre mot de passe.")
        password = await bot.bot.wait_for('message', check=check)
        password = password.content
        await ctx.send("Confirmez-vous vos données d'authentification ? (o/n)")
        answer = await bot.bot.wait_for('message', check=check)
        if answer.content.lower() in 'ouiyes':
            return User(user.id, username, password)
