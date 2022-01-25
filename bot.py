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
        result = ""
        for semester in letters:
            result += semester + " :\n"
            result += "\n".join([f"\t-{ue[0]} : {ue[1]}" for ue in letters[semester]]) + "\n"
        await ctx.send(result)


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
    if not can_check(ctx, semester):
        await ctx.send("Pas le droit de consulter")
        return
    with requests.Session() as session:
        async def init_async(_session):
            init_session(_session)
        await asyncio.gather(
            ctx.send("Connexion au serveur"),
            init_async(session)
        )
        page = get_student_file(session)
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
async def start_ue_watch(ctx, delay=1):
    delay = int(delay)
    await ctx.send(f"Début de l'observation du dossier étudiant. Observation toutes les {delay} secondes")
    t = threading.Thread(target=watch, args=(ctx, delay), daemon=True)
    t.start()
