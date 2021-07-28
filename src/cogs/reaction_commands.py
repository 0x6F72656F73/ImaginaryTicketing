# from datetime import datetime
from typing import Union
import logging

import discord
from discord.ext import commands
from discord.utils import get
# from discord.ext.forms import Form, ReactionForm
# import humanize

from cogs.helpers.actions import CloseTicket, DeleteTicket
from cogs.helpers.views import command_views
from utils.others import Others
from utils.database.db import DatabaseManager as db
import config

log = logging.getLogger(__name__)
guild_ids = [788162899515801637, 861845094415728681]

class MiscCommands(commands.Cog):
    """other useful commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @ commands.command(name="ticket")
    @ commands.has_role(config.ADMIN_ROLE)
    async def ticket(self, ctx: commands.Context):
        """prints a ticket message"""
        await ctx.channel.send("_ _", view=command_views.TicketView())

    @ commands.command(name="create", aliases=["new", "cr"])
    @ commands.cooldown(rate=5, per=10, type=commands.BucketType.default)
    async def create(self, ctx: commands.Context, ticket_type: str = "help", member: discord.Member = None):
        """create a new ticket for the user if non-admin, or with the user specified if admin"""
        admin = get(ctx.guild.roles, name=config.ADMIN_ROLE)
        if admin not in ctx.author.roles:
            member = ctx.author
            epicreactions = Actions(ctx.guild, member,
                                    ctx.channel, 1234)
            await epicreactions.create(ticket_type)
        else:
            if member and member.bot:
                return
            member = member or ctx.author
            epicreactions = Actions(ctx.guild, member,
                                    ctx.channel, 1234)
            await epicreactions.create(ticket_type)

    @ commands.command(name="add", aliases=["a"], help="add a user to a ticket")
    @ commands.has_role(config.ADMIN_ROLE)
    async def add(self, ctx, member: discord.Member):
        """adds a user from a ticket"""

        epicreactions = Actions(ctx.guild, member,
                                ctx.channel, ctx.message.id)

        memids = [member.id for member in ctx.channel.members]
        if member.id in memids:
            emby = await Others.make_embed(0x0000FF, f"User {member.name} already in channel")
            await ctx.channel.send(embed=emby)
            return

        admin = get(ctx.guild.roles, name=config.ADMIN_ROLE)
        if admin in member.roles:
            emby = await Others.make_embed(0x0000FF, f"User {member.name} is an admin")
            await ctx.channel.send(embed=emby)
            return

        await epicreactions.add(member)

        await Others.delmsg(ctx)

    @commands.command(name="remove", aliases=["r", "d"])
    @commands.has_role(config.ADMIN_ROLE)
    async def remove(self, ctx, member: discord.Member):
        """removes a user from a ticket"""

        memids = [member.id for member in ctx.channel.members]
        if member.id not in memids:
            emby = await Others.make_embed(0x0000FF, f"User {member.name} not in channel")
            await ctx.channel.send(embed=emby)
            return
        admin = get(ctx.guild.roles, name=config.ADMIN_ROLE)
        if admin in member.roles:
            emby = await Others.make_embed(0x0000FF, f"User {member.name} is an admin")
            await ctx.channel.send(embed=emby)
            return

        epicreactions = Actions(ctx.guild, member,
                                ctx.channel, ctx.message.id)
        await epicreactions.remove(member)
        await Others.delmsg(ctx)

    @commands.command(name="close", aliases=["cl"])
    async def close(self, ctx):
        """closes a ticket"""
        user_id = db.get_user_id(ctx.channel.id)
        if user_id is None:
            return
        guild = ctx.guild
        admin = get(guild.roles, name=config.ADMIN_ROLE)
        if admin in ctx.author.roles or user_id == ctx.author.id:

            epicreactions = CloseTicket(ctx.guild, ctx.author,
                                        ctx.channel)

            await Others.delmsg(ctx)

            await epicreactions.main()
        else:
            await ctx.channel.send("You do not have enough permissions to run this command")

    # @commands.command(name="close_stats_helper", aliases=["test"])
    # async def test(self, ctx: commands.Context):
    #     old = ctx.channel.created_at
    #     now = datetime.utcnow()
    #     duration = now - old
    #     prettyTime = humanize.precisedelta(
    #         duration, format="%0.0f", minimum_unit="minutes")
    #     emby = discord.Embed(
    #         title="Ticket closed",
    #         description=f"Ticket was closed by self.user.mention",
    #         timestamp=datetime.utcnow(),
    #         color=0x008080)
    #     emby.add_field(name="Time open:",
    #                    value=f"{prettyTime}", inline=True)
    #     # emby.add_field()
    #     await ctx.send(embed=emby)

    @commands.command(name="delete", aliases=["del"])
    @commands.has_role(config.ADMIN_ROLE)
    async def delete(self, ctx):
        """deletes a ticket"""

        epicreactions = DeleteTicket(ctx.guild, ctx.author,
                                     ctx.channel)
        await Others.delmsg(ctx, time=0.0)
        try:
            await epicreactions.main()
        except discord.errors.NotFound:
            pass

    @commands.command(name="reopen", aliases=["re", "reo", "re-open"])
    @commands.has_role(config.ADMIN_ROLE)
    async def reopen(self, ctx):
        """reopens a ticket"""

        epicreactions = Actions(ctx.guild, ctx.author,
                                ctx.channel, ctx.message.id)
        await epicreactions.reopen()

        await Others.delmsg(ctx)

    @commands.command(name="transcript", alias=["tsc"])
    @commands.has_role(config.ADMIN_ROLE)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.default)
    async def transcript(self, ctx, user: discord.User):
        """sends a transcript to a user via DM"""
        #make slash
        await Others.transcript(ctx.channel, user)
        await ctx.channel.send("transcript sent to dms")

    @commands.command(name="autoclose", aliases=["ac"])
    @commands.has_role(config.ADMIN_ROLE)
    async def autoclose(self, ctx, option: str = "off", channel: discord.TextChannel = None):
        """turns the autoclose feature on or off for a give channel"""

        if channel is None:
            channel = ctx.channel
        if option == "off":
            db.update_check("2", channel.id)
            await ctx.channel.send(f"autoclose is now off for {ctx.channel.name}")
        else:
            db.update_check("0", channel.id)
            await ctx.channel.send(f"autoclose is now on for {ctx.channel.name}")

    @commands.command(name="about")
    async def about(self, ctx):
        """returns about info"""

        emby = discord.Embed(title="about",
                             description="This bot was proudly made by 0x6F72656F73#8221 :cookie:")

        await ctx.send(embed=emby)

    def cog_check(self, ctx):
        if not ctx.message.guild:
            raise commands.errors.NoPrivateMessage(
                'Command cannot be used in DMs.')
        return True

def setup(bot: commands.Bot):
    bot.add_cog(MiscCommands(bot))
