import asyncio
import logging

from discord.utils import get
from discord.ext import commands

import config
from utils.others import Others
from utils.database.db import DatabaseManager as db

log = logging.getLogger(__name__)

def is_owner():
    "helper function to check if author is admin"
    async def predicate(ctx):
        return ctx.author.id in config.OWNERS
    return commands.check(predicate)

class Admin(commands.Cog):
    """admin commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shutdown")
    @is_owner()
    async def shutdown(self, ctx):
        """shuts the bot down"""

        embed = Others.Embed(
            description="Shutting down. Bye! :wave:")
        await ctx.send(embed=embed)
        log.warning(f"{ctx.author} is closing the bot")
        await self.bot.close()
        log.warning("successfully closed bot")

    @shutdown.error
    async def shutdown_error(self, ctx, error):
        await ctx.channel.send("you're not an owner :cry:")

    @commands.command(name="purge")
    @commands.has_role(config.ADMIN_ROLE)
    async def purge(self, ctx, limit: int):
        """purges x amount of messages"""

        await ctx.channel.purge(limit=limit + 1)
        msg = await ctx.send(f'Purged {limit} messages')
        await asyncio.sleep(3)
        await msg.delete()

    @commands.command(name="check")
    @commands.has_role(config.ADMIN_ROLE)
    async def check_discord(self, ctx):
        """Checks if all configurations are valid"""
        bot_guild = ctx.guild.get_member(self.bot.user.id)
        checks = {"ticket ping role": bool(get(ctx.guild.roles, name=config.TICKET_PING_ROLE)),
                  "bots role": bool(get(ctx.guild.roles, name=config.BOTS_ROLE)),
                  "channel log category": bool(get(ctx.guild.categories, name=config.LOG_CHANNEL_CATEGORY)),
                  "channel log name": bool(get(ctx.guild.text_channels, name=config.LOG_CHANNEL_NAME)),
                  "is admin": bool(bot_guild.guild_permissions.administrator)}

        def check_all(return_print=False):
            if all(checks.values()):
                return True

            failures = [check for check, status
                        in checks.items() if status is False]

            if return_print:
                return failures
            return False

        failure = check_all()
        if not failure:
            fails = "\n".join(check_all(return_print=True))
            embed = Others.Embed(title="Failed Checks", description=fails)
            await ctx.channel.send(embed=embed)
            return

        await ctx.channel.send("All checks were successful 😎")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do that")
        if isinstance(error, commands.MissingRole):
            await ctx.send("You can't do that!")

def setup(bot):
    bot.add_cog(Admin(bot))
