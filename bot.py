import discord
import requests
import asyncio
from discord.ext import commands
from website_interact.ent_requests import init_session, get_student_file
from website_interact.html_analysis import extract_letters, extract_decisions
from confidential import BOT_TOKEN
from users import User, UserNotFoundError, OverwriteError
import threading

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='!')


def start_bot():
    bot.run(BOT_TOKEN)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


async def send_embed_letters(ctx, letters: dict[str, list[str, str, str]], semester) -> None:
    def get_value(ue_liste):
        return '\n'.join(
            [f"- {ue[0]} : {ue[1]} " + (f"({ue[2]} crédits)" if len(ue) == 3 else "")
             for ue in ue_liste if len(ue) > 1]
        )

    embed = discord.Embed(title="Décisions jurys")
    if semester == 'all':
        for letter in letters:
            embed.add_field(name=letter, value=get_value(letters[letter]), inline=False)
    elif semester == 'last':
        key = list(letters.keys())[-1]
        embed.add_field(name=key, value=get_value(letters[key]), inline=False)
    elif semester not in letters:
        await ctx.send("Semestre non trouvé")
        return
    else:
        print(letters[semester])
        embed.add_field(name=semester, value=get_value(letters[semester]), inline=True)
    await ctx.send(embed=embed)


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


@bot.command()
async def get_decision(ctx, semester: str = 'last') -> None:
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
        decisions = extract_decisions(page)
        await send_embed_decision(ctx, decisions, semester)


async def notify_new_decision(ctx, decision):
    await ctx.send(f"Nouvelle décision :\n{decision}")


def watch(ctx, delay):
    exit_flag = threading.Event()
    with requests.Session() as session:
        init_session(session)
        page = get_student_file(session)
        decisions = extract_decisions(page)
        key = list(decisions.keys())[-1]
        last_decision = decisions[key]
        while True:
            while not exit_flag.wait(delay):
                try:
                    page = get_student_file(session)
                    new_decision = extract_decisions(page)[key]
                    print(new_decision)
                    if last_decision != new_decision:
                        last_decision = new_decision
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(notify_new_decision(ctx, new_decision))
                    loop.close()
                except InterruptedError:
                    pass


@bot.command()
async def start_ue_watch(ctx, delay = 1):
    delay = int(delay)
    await ctx.send(f"Début de l'observation du dossier étudiant. Observation toutes les {delay} secondes")
    t = threading.Thread(target=watch, args=(ctx, delay), daemon=True)
    t.start()


async def dm_register(user) -> User | None:
    ctx = user.dm_channel
    await ctx.send("Vous avez demandé à vous enregistrer. Vos informations personnelles seront stockées sur une base "
                   "de données. Votre mot de passe sera crypté avec une clef accessible uniquement par Thomas  Girod, "
                   "le développeur de ce bot. Ne continuez que si vous lui faites confiance.\n\n Voulez-vous "
                   "poursuivre ? o/n")
    answer: discord.Message = await bot.wait_for('message', check=lambda m: isinstance(m.channel, discord.DMChannel))
    if answer.content.lower() not in 'ouiyes':  # user can answer 'o', 'oui', 'y' or 'yes'
        await ctx.send("Abandon de l'opération")
        return None
    while True:
        await ctx.send("Donnez votre identifiant sur l'ENT.")
        username = await bot.wait_for('message', check=lambda m: isinstance(m.channel, discord.DMChannel))
        username = username.content
        await ctx.send("Donnez votre mot de passe.")
        password = await bot.wait_for('message', check=lambda m: isinstance(m.channel, discord.DMChannel))
        password = password.content
        await ctx.send("Confirmez-vous vos données d'authentification ? (o/n)")
        answer = await bot.wait_for('message', check=lambda m: isinstance(m.channel, discord.DMChannel))
        if answer.content.lower() in 'ouiyes':
            return User(user.id, username, password)


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
