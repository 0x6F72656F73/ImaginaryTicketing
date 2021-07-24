import sys
import os
import platform
import asyncio
import traceback
import logging
from environs import Env

import discord
from discord.ext.commands import Bot
from discord.ext import commands
from pretty_help import PrettyHelp, DefaultMenu
import chat_exporter

from cogs.helpers.views.command_views import *
from utils.runcmds import startlogging

startlogging('tickets.log')


if not os.path.isfile("config.py"):
    sys.exit("'config.py' not found! Please add it and try again.")
else:
    import config

env = Env()
env.read_env()

log = logging.getLogger()
log.info('logging has started')

try:
    import uvloop
except ImportError:
    log.warning("uvloop could not be imported")
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
finally:
    loop = asyncio.get_event_loop()

intents = discord.Intents().all()

try:
    BOT_PREFIX = env.list("BOT_PREFIX")
except TypeError:
    log.exception(
        'please put at least 1 prefix in the format BOT_PREFIX = ["t."]')
    sys.exit()


class TicketBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket_view_added = False
        self.loop = loop

    async def on_ready(self):
        async def status_task():
            while True:
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=(f"great stuff | {BOT_PREFIX[0]}help")))

        self.loop.create_task(status_task())
        if not self.ticket_view_added:
            self.add_view(TicketView())
            self.ticket_view_added = True
        log.info(f"Logged in as {self.user.name}")
        log.info(f"discord.py API version: {discord.__version__}")
        log.info(f"Python version: {platform.python_version()}")
        log.info(
            f"Running on: {platform.system()} {platform.release()} ({os.name})")
        log.info("-------------------")
        chat_exporter.init_exporter(self.user)

    # @self.check
    # async def pog(self):
    #     print('a')


bot = TicketBot(command_prefix=BOT_PREFIX,
                intents=intents, case_insensitive=True)

# @bot.event
# async def on_ready():
#     bot.loop.create_task(status_task())
#     # print(bot.ticket_view_added)
#     if not bot.ticket_view_added:
#         bot.add_view(TicketView())
#         bot.ticket_view_added = True

#     log.info(f"Logged in as {bot.user.name}")
#     log.info(f"discord.py API version: {discord.__version__}")
#     log.info(f"Python version: {platform.python_version()}")
#     log.info(
#         f"Running on: {platform.system()} {platform.release()} ({os.name})")
#     log.info("-------------------")
#     chat_exporter.init_exporter(bot)

# aa = await slash.to_dict()
# log.debug(aa)
# commands = []
# for guild in parsed["guild"]:
#     for command in parsed["guild"][guild]:
#         if command not in commands:
#             commands.add({command.name}) # jes add to embed directly

menu = DefaultMenu(page_left="👈", page_right="👉",
                   active_time=15)

ending_note = f"Type {BOT_PREFIX[0]}help command for more info on a command. \
You can also type {BOT_PREFIX[0]}help category for more info on a category. \
Type {BOT_PREFIX[0]}help_slash for help on slash commands"  # note: make this

bot.help_command = PrettyHelp(
    menu=menu, ending_note=ending_note, sort_commands=True)

if __name__ == "__main__":
    for extension in config.STARTUP_COGS:
        try:
            bot.load_extension(extension)
            extension = extension.replace("cogs.", "")
            log.info(f"Loaded extension '{extension}'")
        except Exception as e:
            exception = f"{type(e).__name__}: {e}"
            extension = extension.replace("cogs.", "")
            log.critical(
                f"Failed to load extension {extension}\n{exception}\n\n")
            logging.exception('Got exception on main handler')
            raise

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot or not message.guild:
        return
    await bot.process_commands(message)
    # if message.guild:
    #     await bot.process_commands(message)
    # else:
    #     await message.author.send("This command does not work in direct messages")

@bot.check
def check_bot_perms(ctx):
    if str(ctx.command) == "check":
        return True
    bot_guild = ctx.guild.get_member(bot.user.id)
    return bot_guild.guild_permissions.administrator

@bot.event
async def on_command_completion(ctx):
    full_command_name = ctx.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    log.info(
        f"Executed {executed_command} command in {ctx.message.channel} by {ctx.message.author} (ID: {ctx.message.author.id})")

@bot.event
async def on_command_error(ctx, error):

    if hasattr(ctx.command, 'on_error'):
        return

    cog = ctx.cog
    if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
        return
    if isinstance(error, commands.errors.NoPrivateMessage):
        await ctx.channel.send("Command cannot be used in DMs.")
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send("Please provide all required arguments")
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send("Command is on cooldown")
        return
    if isinstance(error, commands.MemberNotFound):
        await ctx.channel.send("member not found")
        return
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRole):
        await ctx.channel.send("You do not have enough permissions to run this command")
        return
    if isinstance(error, commands.CheckFailure):
        await ctx.send('Bot does not have administrator permissions.')
        return

    # log.exception(error)
    exc = getattr(error, 'original', error)
    lines = ''.join(traceback.format_exception(
        exc.__class__, exc, exc.__traceback__))
    lines = f'Ignoring exception in command {ctx.command}:\n{lines}'
    log.info(lines)
    await ctx.channel.send(f"{ctx.command.name} was invoked incorrectly.")

def run_bot():
    try:
        token = os.getenv("DISCORD_TOKEN")
    except:
        log.exception(
            "Please create a .env file and enter your DISCORD TOKEN")
        sys.exit()
    bot.run(token)
