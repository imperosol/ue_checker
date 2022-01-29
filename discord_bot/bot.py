import discord
from discord.ext import commands

from discord_bot.aux_functions import send_embed_decision, dm_register, get_letters_semester, get_letters_category, \
    get_student_file_page
from website_interact.html_analysis import extract_decisions
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
    if len(args) == 0:  # default behaviour when no argument : all letters of last semester
        await get_letters_semester(ctx, categories=('CS', 'TM', 'ME', 'EC', 'CT', 'ST', 'HP'))
        return
    first_arg = args[0]
    args = list(set(arg.upper() for arg in args))  # remove eventual duplicates and upper everything
    categories = set(arg for arg in args if arg in ('CS', 'TM', 'ME', 'EC', 'CT', 'HT', 'ST', 'HP'))
    if len(categories) == 0 or 'all_cat' in args:
        categories = ('CS', 'TM', 'ME', 'EC', 'CT', 'ST', 'HP')
    if 'HT' in categories:  # ues HT are named CT in the ENT
        categories.remove('HT')
        categories.add('CT')
    branches = ['TC', 'ISI', 'RT', 'MTE', 'MM', 'GM', 'GI', 'A2I']
    if 'all_sem' in args:
        semesters = branches
    else:
        semesters = list(set(arg for arg in args if any(arg.startswith(branch) for branch in branches)))
    if first_arg in categories or first_arg == 'all_cat':
        await get_letters_category(ctx, semesters, categories)
    else:
        await get_letters_semester(ctx, semesters, categories)


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
