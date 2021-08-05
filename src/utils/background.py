"""
0 = nothing has happened
1 = bot has said 1 message
2 = channel will be ignored
"""

from itertools import chain
from datetime import timedelta
import logging
from typing import Dict

import discord
from discord.ext import commands
from environs import Env
import requests

import cogs.helpers.views.action_views as action_views
import cogs.helpers.actions as actions
from utils.options import Options
from utils.others import Others
from utils.database.db import DatabaseManager as db
import config

log = logging.getLogger(__name__)

class AutoClose(commands.Cog):
    """Autoclose ticket manager"""

    @classmethod
    async def get_message_time(cls, channel: discord.channel.TextChannel):
        """get the total time of the last message send

        Parameters
        ----------
        channel : `str`
            channel to get message from

        Returns:
            duration (int): duration from message creation till now
            message: the message
        """
        try:
            message_list = await channel.history(limit=1).flatten()
            try:
                message = message_list[0]
            except IndexError:
                return
        except discord.errors.NotFound as e:
            log.warning(e)
            return
        else:
            pass
        old = message.created_at
        now = discord.utils.utcnow()
        return message, now - old

    @classmethod
    async def old_ticket_actions(cls, bot: discord.ext.commands.bot.Bot, guild: discord.guild.Guild,
                                 channel: discord.channel.TextChannel, message: discord.message.Message):
        """Check if a channel is old

        If check is 0, send a polite message and set check to 1.
        If check is 1, close the ticket and set check to 0 allowing
        proper control if ticket is reopened.

        Parameters
        ----------
        bot : `discord.commands.bot.Bot`
            the bot\n
        guild : `discord.guild.Guild`
            the guild\n
        channel : `discord.channel.TextChannel`
            the channel\n
        message : `discord.message.Message`
            the latest message\n
        """

        check = db.get_check(channel.id)
        log.info(f"check: {check}- {channel}")

        if check == 1:
            close = actions.CloseTicket(guild, bot, channel, background=True)
            await close.main()
            db.update_check("0", channel.id)

        elif check == 0:
            user_id = db.get_user_id(channel.id)
            member = guild.get_member(int(user_id))
            message = f"If that is all we can help you with {member.mention}, please close this ticket."
            random_admin = await Others.random_admin_member(guild)
            await Others.say_in_webhook(bot, random_admin, channel, random_admin.avatar.url, True, message, return_message=True, view=action_views.CloseView())
            log.info(
                f"{random_admin.name} said the auto close message in {channel.name}")
            db.update_check("1", channel.id)
        else:  # ticket ignored
            pass

    @classmethod
    async def main(cls, bot, **kwargs):
        """check for inactivity in a channel

        Parameters
        ----------
        bot : `[type]`
            [description]\n
        """
        cat = Options.full_category_name("help")
        for guild in bot.guilds:
            if guild.get_member(bot.user.id).guild_permissions.administrator is None:
                return
            safe_tickets_list = list(chain(*db.get_guild_check(guild.id)))
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
                    message, duration = await cls.get_message_time(channel)
                except:
                    continue

                if duration < timedelta(**kwargs):
                    check = db.get_check(channel.id)

                    role = discord.utils.get(
                        guild.roles, name=config.ADMIN_ROLE)
                    people = [member.id for member in role.members]

                    if message.author.id in people and check == 1:
                        db.update_check("0", channel.id)

                elif duration > timedelta(**kwargs):
                    await cls.old_ticket_actions(bot, guild, channel, message)

class ScrapeChallenges():
    """Scraps challenges"""
    @classmethod
    def _setup(cls) -> Dict[str, str]:
        env = Env()
        env.read_env()
        return {'apikey': env.str('apikey')}

    @classmethod
    def main(cls) -> None:
        params = cls._setup()
        req = requests.get(config.BASE_API_LINK +
                           '/challenges/released', params=params)

        challenges = req.json()
        all_challenges = []
        for challenge in challenges:
            ignore = challenge['author'] == config.ADMIN_ROLE
            all_challenges.append(Others.Challenge(
                challenge["id"], challenge["title"], challenge["author"], challenge["category"].split(",")[0], ignore))

        db.refresh_database(all_challenges)

    @classmethod
    def get_user_challenges(cls, discord_id: int):
        params = cls._setup()
        req = requests.get(config.BASE_API_LINK +
                           f'/solves/bydiscordid/{discord_id}', params=params)
        solve_challenges = req.json()
        if not solve_challenges:
            return []
        return [challenge['challenge']['id'] for challenge in solve_challenges]
