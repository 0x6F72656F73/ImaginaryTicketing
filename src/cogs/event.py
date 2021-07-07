import logging

import discord
from discord.ext import commands

import config
from cogs.helpers.actions import Actions
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
            user = self.bot.get_user(user_id)
            channel_id = payload.channel_id
            channel = self.bot.get_channel(channel_id)

            message_id = payload.message_id
            emoji_raw = payload.emoji
            emoji = payload.emoji.name
            ticket_channel_ids = db.get_all_ticket_channels(guild_id)
            epicreactions = Actions(commands.Cog, self.bot, guild, user, channel,
                                    message_id, False, payload, emoji, emoji_raw=emoji_raw)
        except Exception as e:
            channel_log = discord.utils.get(
                guild.text_channels, name=config.LOG_CHANNEL_NAME)
            await channel_log.send("Ticket information error.")
            log.exception(str(e))
            return
        # make classes out of these (eventually 3 tables so another class maybe)
        if emoji in config.EMOJIS:
            # create a new ticket
            await epicreactions.create()

        if channel_id in ticket_channel_ids and emoji == "🔒" and user.bot is False:  # close ticket logic
            await epicreactions.close()

        if channel_id in ticket_channel_ids and emoji == "🔓" and user.bot is False:  # re-open ticket logic
            await epicreactions.reopen_ticket()

        if channel_id in ticket_channel_ids and emoji == "⛔" and user.bot is False:  # delete ticket logic
            await epicreactions.delete()


def setup(bot):
    bot.add_cog(Event(bot))
