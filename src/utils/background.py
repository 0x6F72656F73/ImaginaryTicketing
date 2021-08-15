"""
0 = nothing has happened
1 = bot has said 1 message
2 = channel will be ignored
"""

from datetime import timedelta
import json
from typing import Dict, List
import logging

import discord
from discord.ext import commands
from environs import Env
import aiohttp

import cogs.helpers.views.action_views as action_views
import cogs.helpers.actions as actions
from utils.options import Options
from utils.utility import Utility, UI, Challenge
from utils.database.db import DatabaseManager as db
import config

log = logging.getLogger(__name__)

class AutoClose(commands.Cog):
    """Autoclose ticket manager"""

    @classmethod
    async def get_message_time(cls, channel: discord.TextChannel):
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
    async def old_ticket_actions(cls, bot: commands.bot.Bot, guild: discord.guild.Guild,
                                 channel: discord.TextChannel, message: discord.message.Message):
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
        channel : `discord.TextChannel`
            the channel\n
        message : `discord.message.Message`
            the latest message\n
        """

        check = int(db.get_check(channel.id))
        log.info(f"check: {check}- {channel}")

        if check == 1:
            close = actions.CloseTicket(guild, bot, channel, background=True)
            await close.main()
            db.update_check("0", channel.id)

        elif check == 0:
            user_id = db.get_user_id(channel.id)
            member = guild.get_member(int(user_id))
            message = f"If that is all we can help you with {member.mention}, please close this ticket."
            random_admin = await Utility.random_admin_member(guild)
            await Utility.say_in_webhook(bot, random_admin, channel, random_admin.avatar.url, True, message, return_message=True, view=action_views.CloseView())
            log.info(
                f"{random_admin.name} said the auto close message in {channel.name}")
            db.update_check("1", channel.id)
        else:  # ticket ignored
            pass

    @classmethod
    async def main(cls, bot: commands.bot.Bot, **kwargs):
        """check for inactivity in a channel

        Parameters
        ----------
        bot : `[type]`
            [description]\n
        """
        cat = Options.full_category_name("help")
        for guild in bot.guilds:
            safe_tickets_list = db.get_guild_safe_tickets(guild.id)
            category = discord.utils.get(guild.categories, name=cat)
            if category is None:
                return
            channels = category.text_channels
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
                    check = int(db.get_check(channel.id))

                    role = discord.utils.get(
                        guild.roles, name=config.ADMIN_ROLE)
                    people = [member.id for member in role.members]

                    if message.author.id in people and check == 1:
                        db.update_check("0", channel.id)

                elif duration > timedelta(**kwargs):
                    await cls.old_ticket_actions(bot, guild, channel, message)

class ScrapeChallenges():
    """Scrapes challenges"""
    @classmethod
    def _setup(cls) -> Dict[str, str]:
        env = Env()
        env.read_env()
        return {'apikey': env.str('apikey')}

    @classmethod
    async def main(cls, bot: commands.bot.Bot) -> None:
        params = cls._setup()
        async with aiohttp.ClientSession() as session:
            async with session.get(config.BASE_API_LINK +
                                   '/challenges/released', params=params) as req:
                challenges = await req.json()
                all_challenges = []
                for challenge in challenges:
                    ignore = bool(challenge['author'] == config.ADMIN_ROLE)
                    all_challenges.append(Challenge(
                        challenge["id"], challenge["title"], challenge["author"], challenge["category"].split(",")[0], ignore))

                db.refresh_database_ch(all_challenges)
                await UpdateHelpers.main(bot)

    @classmethod
    async def get_user_challenges(cls, discord_id: int) -> List[int]:
        params = cls._setup()
        async with aiohttp.ClientSession() as session:
            async with session.get(config.BASE_API_LINK +
                                   f'/solves/bydiscordid/{discord_id}', params=params) as req:
                solve_challenges = await req.json()
                if not solve_challenges:
                    return []
                return [challenge['challenge']['id'] for challenge in solve_challenges]

class UpdateHelpers():
    @staticmethod
    async def main(bot: commands.bot.Bot):
        for guild in bot.guilds:
            if guild.id == 788162899515801637:
                helper_role = discord.utils.get(
                    guild.roles, name=config.HELPER_ROLE)
                for helper in helper_role.members:
                    solved_challenge_ids = await ScrapeChallenges.get_user_challenges(
                        helper.id)
                    for ch_id in solved_challenge_ids:
                        db.update_helper_ch(helper.id, ch_id)

    @classmethod
    async def add_helper_to_channel(cls, ticket_channel: discord.TextChannel, user_id: int):
        author = ticket_channel.guild.get_member(user_id)
        if author is None or author in ticket_channel.members:
            return
        await ticket_channel.set_permissions(author, read_messages=True,
                                             send_messages=True)

    @classmethod
    async def add_helpers(cls, bot: commands.bot.Bot):
        for guild in bot.guilds:
            if guild.id == 788162899515801637:
                for channel in db.get_all_help_channels(guild.id):
                    if (channel_ := guild.get_channel(channel)):
                        helpers = db.get_helpers_from_title(
                            channel_.topic.split(" -")[0])
                        if helpers is None:
                            await UI.log_to_logs(
                                "Challenge not found", channel_)
                            continue
                        helpers = json.loads(helpers[0])
                        for helper in helpers:
                            await cls.add_helper_to_channel(channel_, helper)
