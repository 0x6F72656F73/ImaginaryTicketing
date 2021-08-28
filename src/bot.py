import os
import platform
import asyncio
import traceback
import logging
import environs

import discord
from discord.ext import commands
import pretty_help
import chat_exporter

from cogs.helpers import views
from utils.logging_setup import start_logging

start_logging('tickets.log')


if not os.path.isfile("config.py"):
    raise RuntimeError("config.py not found")
else:
    import config

env = environs.Env()
env.read_env()

log = logging.getLogger()
log.info('logging has started')

try:
    import uvloop
except ImportError:
    log.warning("'uvloop' could not be imported")
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
finally:
    loop = asyncio.get_event_loop()

BOT_PREFIX = env.list("BOT_PREFIX")


class TicketBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop = loop
        self.persistent_views_added = False
        self.add_check(self.check_bot_perms)

        ending_note = f"Type {BOT_PREFIX[0]}help command for more info on a command. \
You can also type {BOT_PREFIX[0]}help category for more info on a category. \
Type {BOT_PREFIX[0]}help_slash for help on slash commands"  # note: make this

        menu = pretty_help.DefaultMenu(page_left="👈", page_right="👉",
                                       active_time=15)
        self.help_command = pretty_help.PrettyHelp(
            menu=menu, ending_note=ending_note, sort_commands=True)

        for extension in config.admin['startup_cogs']:
            try:
                self.load_extension(extension)
                extension = extension.replace("cogs.", "")
                log.info(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                extension = extension.replace("cogs.", "")
                log.critical(
                    f"Failed to load extension {extension}\n{exception}\n\n")
                logging.exception('Got exception on main handler')
                raise

    @classmethod
    def create(cls) -> "TicketBot":
        return cls(
            activity=discord.Activity(type=discord.ActivityType.watching, name=(
                f"great stuff | {BOT_PREFIX[0]}help")),
            command_prefix=commands.when_mentioned_or(*BOT_PREFIX),
            case_insensitive=True,
            strip_after_prefix=True,
            allowed_mentions=discord.AllowedMentions(everyone=False),
            intents=discord.Intents().all(),
        )

    async def on_ready(self):
        if not self.persistent_views_added:
            views.setup(self)
            self.persistent_views_added = True
            log.info("Loaded all views")
        log.info(f"Logged in as {self.user.name}")
        log.info(f"discord.py API version: {discord.__version__}")
        log.info(f"Python version: {platform.python_version()}")
        log.info(
            f"Running on: {platform.system()} {platform.release()} ({os.name})")
        log.info("-------------------")
        chat_exporter.init_exporter(self.user)

    async def on_message(self, message):
        if message.author == self.user or message.author.bot or not message.guild:
            return
        await self.process_commands(message)
        # if message.guild:
        #     await bot.process_commands(message)
        # else:
        #     await message.author.send("This command does not work in direct messages")

    async def on_command_completion(self, ctx):
        full_command_name = ctx.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        log.info(
            f"Executed {executed_command} command in {ctx.message.channel} by {ctx.message.author} (ID: {ctx.message.author.id})")

    async def on_command_error(self, ctx, error):
        if hasattr(ctx.command, 'on_error'):
            return
        cog = ctx.cog
        if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
            return
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.errors.NoPrivateMessage):
            return await ctx.channel.send("Command cannot be used in DMs.")
        if isinstance(error, commands.errors.ChannelNotFound):
            return await ctx.channel.send(f"Channel {error.argument} not found")
        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.channel.send("Command is on cooldown")
        if isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            return await ctx.channel.send("User not found")
        if isinstance(error, commands.MissingRole):
            return await ctx.channel.send("You need to buy more perms from dollar store")
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.channel.send("Please provide all required arguments")
        if isinstance(error, commands.errors.BadUnionArgument):
            return await ctx.channel.send('Destination is neither a valid user nor a valid TextChannel')
        if isinstance(error, commands.CheckFailure):
            return await ctx.send('Bot does not have administrator permissions.')

        exc = getattr(error, 'original', error)
        exception_traceback = ''.join(traceback.format_exception(
            exc.__class__, exc, exc.__traceback__))
        lines = f'Ignoring exception in command {ctx.command}:\n{exception_traceback}'
        log.info(lines)
        await ctx.channel.send(f"{ctx.command.name} was invoked incorrectly.")

    def check_bot_perms(self, ctx):
        if str(ctx.command) == "check":
            return True
        bot_guild = ctx.guild.get_member(self.user.id)
        return bot_guild.guild_permissions.administrator

def run_bot():
    token = env.str("DISCORD_TOKEN")
    instance = TicketBot.create()

    instance.run(token)


run_bot()
