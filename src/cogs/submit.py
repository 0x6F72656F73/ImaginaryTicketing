import logging

import discord
from discord.ext import commands

import config
from utils.others import Others

log = logging.getLogger(__name__)

class MiscCommands(commands.Cog):
    """**Unimplemented** user say and say member commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="say")
    async def say(self, ctx, *, message):
        """says a message through a webhook"""

        await Others.say_in_webhook(self.bot, ctx.author, ctx.channel, ctx.avatar.url, False, message)
        await ctx.message.delete()

    @commands.command(name="saymember", aliases=["saym"])
    @commands.has_role(config.ADMIN_ROLE)
    async def saymember(self, ctx, member: discord.User, *, message):
        """says a message through a webhook through the specified user"""

        await Others.say_in_webhook(self.bot, member, ctx.channel, member.avatar.url, False, message)
        await ctx.message.delete()

    @commands.command(name="about")
    async def about(self, ctx):
        """returns about info"""

        emby = discord.Embed(title="about",
                             description="This bot was proudly made by 0x6F72656F73#8221 :cookie:")

        await ctx.send(embed=emby)

def setup(bot: commands.Bot):
    bot.add_cog(MiscCommands(bot))
