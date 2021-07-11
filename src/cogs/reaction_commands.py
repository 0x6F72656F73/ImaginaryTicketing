# from datetime import datetime
from typing import Optional
import logging

import discord
from discord.ext import commands
from discord.utils import get
# from discord.ext.forms import Form, ReactionForm
# import humanize

from discord_slash import SlashContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from discord_slash.cog_ext import cog_slash

import config
from cogs.helpers.actions import Actions
from utils.others import Others
from utils.database.db import DatabaseManager as db

log = logging.getLogger(__name__)
guild_ids = [788162899515801637, 861845094415728681]

class MiscCommands(commands.Cog):
    """other useful commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @cog_slash(name="testaa", description="This is just a test command, nothing more.", guild_ids=guild_ids,
    #            options=[create_option(name="optone", description="This is the first option we have.", option_type=6, required=True)])
    # async def test(self, ctx, optone: str):
    #     await ctx.send(content=f"I got you, you said {optone}!")

    @cog_slash(name="ticket", description="prints a ticket message", guild_ids=guild_ids)
    @commands.has_role(config.ADMIN_ROLE)
    async def ticket(self, ctx):
        """prints a ticket message"""
        buttons = [
            create_button(
                style=ButtonStyle.primary,
                label="help",
                custom_id='help'
            ),
            create_button(
                style=ButtonStyle.success,
                label="submit",
                custom_id='submit'
            ),
            create_button(
                style=ButtonStyle.danger,
                label="misc",
                custom_id='misc'
            ),
        ]
        action_row = create_actionrow(*buttons)
        await ctx.send("_ _", components=[action_row])

    # @cog_slash(name="create", description="create a new ticket for the user if non-admin, or with the user specified if admin", guild_ids=guild_ids)
    # @commands.cooldown(rate=5, per=10, type=commands.BucketType.default)
    # async def create(self, ctx, member: Optional[discord.Member] = None, type_: str = "help",):
    #     """create a new ticket for the user if non-admin, or with the user specified if admin"""
    #     if member:
    #         if member.bot:
    #             await ctx.channel.send("tickets cannot be created for bots")
    #             return
    #     admin = get(ctx.guild.roles, name=config.ADMIN_ROLE)
    #     if admin not in ctx.author.roles:
    #         member = ctx.author
    #         epicreactions = Actions(commands.Cog, self.bot, ctx.guild, member,
    #                                 ctx.channel, ctx.message.id, type_)
    #         await epicreactions.create(True)
    #     else:
    #         member = member or ctx.author
    #         epicreactions = Actions(commands.Cog, self.bot, ctx.guild, member,
    #                                 ctx.channel, ctx.message.id, type_)
    #         await epicreactions.create(True)
    #     # await Others.delmsg(ctx)

    # @create.error
    # async def create_error(self, ctx, error):
    #     if isinstance(error, commands.MemberNotFound):
    #         user = error.argument
    #         await ctx.channel.send(f"member {user} does not exist")

    @commands.command(name="add", aliases=["a"], help="add a user to a ticket", usage="add <user>")
    @commands.has_role(config.ADMIN_ROLE)
    async def add(self, ctx, member: discord.Member):
        """adds a user from a ticket"""

        epicreactions = Actions(commands.Cog, self.bot, ctx.guild, member,
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

        epicreactions = Actions(commands.Cog, self.bot, ctx.guild, member,
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

            epicreactions = Actions(commands.Cog, self.bot, ctx.guild, ctx.author,
                                    ctx.channel, ctx.message.id)

            await Others.delmsg(ctx)

            await epicreactions.close()
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
    #     # emby.add_field()  # add to sql people who were added(`added` is a column, and everytiem added just insert or smth, and over here jut do select count(1)
    #     await ctx.send(embed=emby)

    # @commands.command(name="close_stats_helper", aliases=["test"])
    # async def test(self, ctx):

    #     epicreactions = Actions(commands.Cog, self.bot, ctx.guild.id, ctx.guild, ctx.author.id, ctx.author,
    #                                    ctx.channel.id, ctx.channel, ctx.message.id,)

    #     await epicreactions.close_stats_helper()

    @commands.command(name="delete", aliases=["del"])
    @commands.has_role(config.ADMIN_ROLE)
    async def delete(self, ctx):
        """deletes a ticket"""

        epicreactions = Actions(commands.Cog, self.bot, ctx.guild, ctx.author,
                                ctx.channel, ctx.message.id)
        await Others.delmsg(ctx, time=0.0)
        try:
            await epicreactions.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="reopen", aliases=["re", "reo", "re-open"])
    @commands.has_role(config.ADMIN_ROLE)
    async def reopen(self, ctx):
        """reopens a ticket"""

        epicreactions = Actions(commands.Cog, self.bot, ctx.guild, ctx.author,
                                ctx.channel, ctx.message.id)
        await epicreactions.reopen_ticket()

        await Others.delmsg(ctx)

    @commands.command(name="transcript", alias=["tsc"])
    @commands.has_role(config.ADMIN_ROLE)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.default)
    async def transcript(self, ctx, member: discord.Member):
        """sends a transcript to a user in DMS"""

        await Others.transcript(ctx.channel, member)
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
