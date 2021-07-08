import asyncio
import logging

import discord
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
        """shutdowns the bot"""

        embed = discord.Embed(
            description="Shutting down. Bye! :wave:",
            color=0x00FF00
        )
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
        clearmsg = await ctx.send(f'Cleared {limit} messages')
        await asyncio.sleep(3)
        await clearmsg.delete()

    @commands.command(name="setticketmessage", aliases=['stm', 'sm'])
    @commands.has_role(config.ADMIN_ROLE)
    async def setticketid(self, ctx, ticket_id: str):
        """sets a ticket message"""

        try:
            db._raw_insert(
                "INSERT into tickets (guild_id, ticket_id) VALUES($1,$2) ON CONFLICT(ticket_id) DO UPDATE SET ticket_id=excluded.ticket_id;", (ctx.guild.id, ticket_id,))
            conf = await ctx.channel.send("ticket message was set")
            await asyncio.sleep(5)
            await conf.delete()
        except Exception as e:
            log.exception(f"{e}")
            await ctx.channel.send("ticket message could not be set")

        await Others.delmsg(ctx, time=2)

    @commands.command(name="deleteticketmessage", aliases=["dtm", "dm"])
    @commands.has_role(config.ADMIN_ROLE)
    async def delete_ticket_id(self, ctx, ticket_id: str):
        """deletes a ticket message"""

        try:
            db._raw_delete(
                "DELETE FROM tickets WHERE guild_id = $1 AND ticket_id = $2", (ctx.guild.id, ticket_id,))
            await ctx.channel.send("ticket message was be deleted")
        except Exception as e:
            log.exception(f"{e}")
            await ctx.channel.send("ticket message could not be deleted")

        await Others.delmsg(ctx)

    @commands.command(name="check")
    @commands.has_role(config.ADMIN_ROLE)
    async def check_discord(self, ctx):
        """Checks if all configurations are valid"""
        bot_guild = ctx.guild.get_member(self.bot.user.id)
        checks = {"ticket ping role": bool(get(ctx.guild.roles, name=config.TICKET_PING_ROLE)),
                  "channel log category": bool(get(ctx.guild.categories, name=config.LOG_CHANNEL_CATEGORY)),
                  "channel log name": bool(get(ctx.guild.text_channels, name=config.LOG_CHANNEL_NAME)),
                  "is admin": bool(bot_guild.guild_permissions.administrator)}

        def check_all(return_print=False):
            if all(checks.values()):
                return True

            failures = []
            for check, status in checks.items():
                if status is False:
                    failures.append(check)

            if return_print:
                return failures
            return False

        failure = check_all()
        if not failure:
            fails = "\n".join(check_all(return_print=True))
            emby = discord.Embed(title="Failed Checks", description=fails)
            await ctx.channel.send(embed=emby)
            return

        await ctx.channel.send("All checks were successful 😎")

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You can't do that")
        if isinstance(error, commands.MissingRole):
            await ctx.send("You can't do that!")

def setup(bot):
    bot.add_cog(Admin(bot))
