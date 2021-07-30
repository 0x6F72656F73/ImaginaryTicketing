import logging

import discord
from discord.ext import commands
from discord.utils import get

import cogs.helpers.actions as actions
from utils.others import Others
from cogs.helpers.views import command_views
from utils.database.db import DatabaseManager as db
from utils.background import ScrapeChallenges
import config

log = logging.getLogger(__name__)
guild_ids = [788162899515801637, 861845094415728681]

class TicketCommands(commands.Cog):
    """other useful commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="ticket")
    @commands.has_role(config.ADMIN_ROLE)
    async def ticket(self, ctx: commands.Context):
        """prints a ticket message"""
        await ctx.channel.send("_ _", view=command_views.TicketView())
        await Others.delmsg(ctx)

    @commands.command(name="create", aliases=["new", "cr"])
    @commands.cooldown(rate=5, per=10, type=commands.BucketType.default)
    async def create(self, ctx: commands.Context, ticket_type: str = "help", member: discord.Member = None):
        """create a new ticket for the user if non-admin, or with the user specified if admin"""
        if ticket_type not in {'help', 'submit', 'misc'}:
            await ctx.channel.send("possible ticket types are help, submit, and misc")
            return
        admin = get(ctx.guild.roles, name=config.ADMIN_ROLE)
        if admin not in ctx.author.roles:
            member = ctx.author
            create_ticket = actions.CreateTicket(
                ticket_type, None, ctx.guild, member, ctx.channel)
        else:
            if member and member.bot:
                await ctx.channel.send("tickets cannot be created for bots")
                return
            member = member or ctx.author
            create_ticket = actions.CreateTicket(
                ticket_type, None, ctx.guild, member, ctx.channel)
        await create_ticket.main()
        await Others.delmsg(ctx)

    @commands.command(name="add", aliases=["a"], help="add a user to a ticket")
    @commands.has_role(config.ADMIN_ROLE)
    async def add(self, ctx, member: discord.Member):
        """adds a user from a ticket"""

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

        await actions.Utility.add(ctx.channel, member)
        await Others.delmsg(ctx)

    @commands.command(name="remove", aliases=["r"])
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

        await actions.Utility.remove(ctx.channel, member)
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

            epicreactions = actions.CloseTicket(ctx.guild, ctx.author,
                                                ctx.channel)
            await Others.delmsg(ctx)
            await epicreactions.main()
        else:
            await ctx.channel.send("You do not have enough permissions to run this command")

    @commands.command(name="delete", aliases=["del"])
    @commands.has_role(config.ADMIN_ROLE)
    async def delete(self, ctx):
        """deletes a ticket"""

        delete_ticket = actions.DeleteTicket(ctx.guild, ctx.author,
                                             ctx.channel)
        try:
            await delete_ticket.main()
        except discord.errors.NotFound:
            pass

    @commands.command(name="reopen", aliases=["re", "reo", "re-open"])
    @commands.has_role(config.ADMIN_ROLE)
    async def reopen(self, ctx):
        """reopens a ticket"""
        reopen_ticket = actions.ReopenTicket(ctx.guild, ctx.author,
                                             ctx.channel)
        await reopen_ticket.main()

        await Others.delmsg(ctx)

    @commands.command(name="transcript", alias=["tsc"])
    @commands.has_role(config.ADMIN_ROLE)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.default)
    async def transcript(self, ctx, user: discord.User):
        """sends a transcript to a user via DM"""

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

    @commands.command(name="refresh", aliases=["ref"])
    @commands.has_role(config.ADMIN_ROLE)
    async def refresh(self, ctx):
        """refreshes challenges from the api"""
        ScrapeChallenges.main()
        await ctx.channel.send("challenges refreshed")
        await Others.delmsg(ctx)

    def cog_check(self, ctx):
        if not ctx.message.guild:
            raise commands.errors.NoPrivateMessage(
                'Command cannot be used in DMs.')
        return True

def setup(bot: commands.Bot):
    bot.add_cog(TicketCommands(bot))
