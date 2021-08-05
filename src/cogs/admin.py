import logging

from discord.ext import commands

import config
from utils.others import Others

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

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do that")

def setup(bot):
    bot.add_cog(Admin(bot))
