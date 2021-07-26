import logging

import discord
from discord.ext import commands

import config
# from cogs.helpers.actions import CreateTicket
from utils.database.db import DatabaseManager as db

log = logging.getLogger(__name__)

class Event(commands.Cog):
    """handles reactions"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.raw_models.RawReactionActionEvent):
        """if an emoji is in config.emojis' create a ticket. etc.

        Parameters
        ----------
        payload : discord.raw_models.RawReactionActionEvent
            the emoji
        """

        guild_id = payload.guild_id
        guild = self.bot.get_guild(guild_id)
        try:
            # get information
            user_id = payload.user_id
            user = guild.get_member(user_id)
            channel_id = payload.channel_id
            channel = self.bot.get_channel(channel_id)

            message_id = payload.message_id
            emoji = payload.emoji.name
            ticket_channel_ids = db.get_all_ticket_channels(guild_id)
            epicreactions = Actions(guild, user, channel, message_id)
        except Exception as e:
            channel_log = discord.utils.get(
                guild.text_channels, name=config.LOG_CHANNEL_NAME)
            await channel_log.send("Ticket information error.")
            log.exception(str(e))
            return

        # make classes out of these (eventually 3 tables so another class maybe)
        if emoji in config.EMOJIS:
            await epicreactions.create('help')

        if channel_id in ticket_channel_ids and emoji == "🔒" and user.bot is False:
            await epicreactions.close()

        if channel_id in ticket_channel_ids and emoji == "🔓" and user.bot is False:
            await epicreactions.reopen()

        if channel_id in ticket_channel_ids and emoji == "⛔" and user.bot is False:
            admin_role = discord.utils.get(
                guild.roles, name=config.ADMIN_ROLE)
            if admin_role in user.roles:
                await epicreactions.delete()


def setup(bot):
    bot.add_cog(Event(bot))
