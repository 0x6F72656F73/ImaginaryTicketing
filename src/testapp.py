from discord.ext import commands
from discord import Intents
from discord_slash import SlashCommand

bot = commands.Bot(intents=Intents.all(),
                   command_prefix="!", case_insensitive=True)
slash = SlashCommand(bot, sync_commands=True)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

bot.load_extension("cogs.test_cog")

@bot.command(name="r")
async def reload_cog(ctx):
    bot.reload_extension("cogs.test_cog")
    await ctx.channel.send("cog reloaded successfully")

@bot.event
async def on_message(message):
    await bot.process_commands(message)

bot.run("ODM5NjM0MTAxNDgwMzI1MjEw.YJMgMQ.PjTrxajGxBby-xXsvJ6BONjSxS0")