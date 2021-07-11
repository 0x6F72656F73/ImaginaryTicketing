"""
0 = nothing has happened
1 = bot has said 1 message
2 = channel will be ignored
"""

from itertools import chain
from datetime import datetime, timedelta
import logging

import discord
from discord.ext import commands

import config
from cogs.helpers.actions import Actions
from utils.options import Options
from utils.others import Others
from utils.database.db import DatabaseManager as db

log = logging.getLogger(__name__)

class Background(commands.Cog):
    """Background Task Manager"""

    @staticmethod
    async def get_message_time(channel: discord.channel.TextChannel):
        """get the total time of the last message send

        ### Args:
            channel (str): channel to get message from

        Returns:
            duration (int): duration from message creation till now
            message: the message
        """
        try:
            message_list = await channel.history(limit=1).flatten()
            try:
                message = message_list[0]
            except IndexError:
                log.info(f"no message in {channel.name}")
                return
        except discord.errors.NotFound as e:
            log.warning(e)
            return
        else:
            pass  # nothing to do
        old = message.created_at
        now = datetime.utcnow()
        return message, now - old

    @staticmethod
    async def old_ticket_actions(bot: discord.ext.commands.bot.Bot, guild: discord.guild.Guild,
                                 channel: discord.channel.TextChannel, message: discord.message.Message):
        """Check if a channel is old

        If check is 0, send a polite message and set check to 1.
        If check is 1, close the ticket and set check to 0 allowing
        proper control if ticket is reopened.

        Parameters
        ----------
        bot : `discord.ext.commands.bot.Bot`
            the bot\n
        guild : `discord.guild.Guild`
            the guild\n
        channel : `discord.channel.TextChannel`
            the channel\n
        message : `discord.message.Message`
            the latest message\n
        """

        check = db.get_check(channel.id)
        log.info(f"check: {check}")

        if check == 1:
            epicreactions = Actions(commands.Cog, bot, guild.id, guild, bot.user.id, bot,
                                    channel.id, channel, message.id, True, bot, emoji=None, background=True)
            await epicreactions.close()
            db.update_check("0", channel.id)

        elif check == 0:
            user_id = db.get_user_id(channel.id)
            member = guild.get_member(int(user_id))
            message = f"If that is all we can help you with {member.mention}, please close this ticket."
            random = await Others.random_member_webhook(guild)
            sent_message = await Others.say_in_webhook(random, channel, random.avatar_url, True, message, return_message=True)
            await sent_message.add_reaction("🔒")
            log.info(f"{random.name} said the message in {channel.name}")
            db.update_check("1", channel.id)
        else:  # ticket ignored
            pass

    @staticmethod
    async def inactivity(bot, **kwargs):
        """check for inactivity in a channel

        Parameters
        ----------
        bot : `[type]`
            [description]\n
        """
        cat = Options.full_category_name("help")
        for guild in bot.guilds:
            bot_guild = guild.get_member(bot.user.id)
            if bot_guild.guild_permissions.administrator is None:
                return
            safe_tickets = db.get_guild_check(guild.id)
            safe_tickets_list = list(chain(*safe_tickets))
            category = discord.utils.get(guild.categories, name=cat)
            if category is None:
                return
            channels = category.channels
            for channel in channels:
                log.debug(channel.name)
                status = db.get_status(channel.id)
                if channel.id in safe_tickets_list or status == "closed" or status is None:
                    continue
                try:
                    status = db.get_status(channel.id)
                except:
                    return

                try:
                    message, duration = await Background.get_message_time(channel)
                except:
                    return

                if duration < timedelta(**kwargs):
                    # print("activity detected")
                    check = db.get_check(channel.id)

                    role = discord.utils.get(
                        guild.roles, name=config.ADMIN_ROLE)
                    people = [member.id for member in role.members]

                    if message.author.id in people and check == 1:
                        db.update_check("0", channel.id)

                elif duration > timedelta(**kwargs):
                    # print("no activity detected")
                    await Background.old_ticket_actions(bot, guild, channel, message)
