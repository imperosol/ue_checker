import discord
import requests
import asyncio
from discord.ext import commands
from ent_requests import init_session, get_student_file
from html_analysis import get_letters, extract_decisions
from confidential import BOT_TOKEN
import threading

client = discord.Client()
bot = commands.Bot(command_prefix='!')


def start_bot():
    bot.run(BOT_TOKEN)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')


def can_check(ctx: discord.ext.commands.Context, semester: str):
    if ctx.author.id == '423937066620157953':
        return True
    else:
        return semester in ('last', 'TC1', 'TC2')


# def ntm():


@bot.command()
async def test(ctx):
    if not can_check(ctx, "TC3"):
        await ctx.send("Pas le droit de consulter")
        return
    with requests.Session() as session:
        await asyncio.gather(
            ctx.send("Connexion au serveur"),
            init_session(session)
        )
        threading.Thread(target=asyncio.run, args=[ctx.send("Getting result")]).start()
        letters = get_letters(get_student_file(session))
        print(letters)
        result = ""
        for semester in letters:
            result += semester + " :\n"
            result += "\n".join([f"\t-{ue[0]} : {ue[1]}" for ue in letters[semester]]) + "\n"
        await ctx.send(result)


async def send_embed_decision(ctx, decisions: dict[str, str], semester):
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
async def get_decision(ctx, semester = 'last'):
    semester = semester.replace(' ', '')
    if not can_check(ctx, semester):
        await ctx.send("Pas le droit de consulter")
        return
    with requests.Session() as session:
        await asyncio.gather(
            ctx.send("Connexion au serveur"),
            init_session(session)
        )
        decisions = extract_decisions(get_student_file(session))
        await send_embed_decision(ctx, decisions, semester)


def watch(delay):
    exit_flag = threading.Event()
    while True:
        while not exit_flag.wait(delay):
            try:
                print('yo')
            except InterruptedError:
                pass


@bot.command()
async def start_ue_watch(ctx, delay):
    await ctx.send(f"Début de l'observation du dossier étudiant. Observation toutes les {delay} secondes")
    t = threading.Thread(target=watch, args=(1,), daemon=True)
    t.start()
