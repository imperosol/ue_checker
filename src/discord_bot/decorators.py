from discord.ext import commands


def work_in_progress():
    def predicate(ctx):
        return ctx.message.author.id == 423937066620157953

    return commands.check(predicate)
