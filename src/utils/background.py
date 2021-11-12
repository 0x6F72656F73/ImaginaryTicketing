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
from utils import types, exceptions
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
    async def old_ticket_actions(cls, bot: commands.Bot, guild: discord.Guild,
                                 channel: discord.TextChannel, message: discord.Message):
        """Check if a channel is old

        If check is 0, send a polite message and set check to 1.
        If check is 1, close the ticket and set check to 0 allowing
        proper control if ticket is reopened.

        Parameters
        ----------
        bot : `discord.commands.Bot`
            the bot\n
        guild : `discord.guild.Guild`
            the guild\n
        channel : `discord.TextChannel`
            the channel\n
        message : `discord.message.Message`
            the latest message\n
        """
        try:
            check = int(db.get_check(channel.id))
        except ValueError as e:
            log.info(e.args[0])
            return
        log.info(f"check: {check}- {channel}")

        if check == 1:
            close = actions.CloseTicket(guild, bot, channel, background=True)
            await close.main(inactivity=True)
            db.update_check("0", channel.id)

        elif check == 0:
            try:
                user_id = db.get_user_id(channel.id)
            except ValueError as e:
                return log.info(e.args[0])
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
    async def main(cls, bot: commands.Bot, **kwargs):
        """check for inactivity in a channel

        Parameters
        ----------
        bot : `discord.commands.Bot`
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
                try:
                    status = db.get_status(channel.id)
                except ValueError as e:
                    log.info(e.args[0])
                    continue

                if channel.id in safe_tickets_list or status == "closed" or status is None:
                    continue

                try:
                    message, duration = await cls.get_message_time(channel)
                except:
                    continue

                if duration < timedelta(**kwargs):
                    try:
                        check = int(db.get_check(channel.id))
                    except ValueError as e:
                        log.info(e.args[0])
                        continue

                    admin = discord.utils.get(
                        guild.roles, name=config.roles['admin'])
                    people = [member.id for member in admin.members]

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
    async def _fetch(cls, client: aiohttp.ClientSession, url: str, params=None) -> Dict[str, str]:
        async with client.get(url, params=params) as resp:
            if not resp.status == 200:
                log.warning("Fetching %s failed", url)
                return []
            return await resp.json()

    @classmethod
    async def fetch_challenges(cls):
        params = cls._setup()
        async with aiohttp.ClientSession() as session:
            return await cls._fetch(session, config.api["base_link"] +
                                    '/challenges/released', params=params)

    @classmethod
    async def main(cls, bot: commands.Bot) -> None:
        challenges = await cls.fetch_challenges()
        all_challenges = []
        for challenge in challenges:
            ignore = bool(challenge['author'] == config.roles['admin'])
            all_challenges.append(Challenge(
                challenge["id"], challenge["title"], challenge["author"], challenge["category"].split(",")[0], ignore))

        db.refresh_database_ch(all_challenges)
        await UpdateHelpers.main(bot)

    @classmethod
    async def get_user_challenges(cls, discord_id: int) -> List[int]:
        params = cls._setup()
        async with aiohttp.ClientSession() as session:
            solve_challenges = await cls._fetch(session, config.api["base_link"] +
                                                f'/solves/bydiscordid/{discord_id}', params=params)
            try:
                team_id = solve_challenges[0]["team"]["id"]
            except IndexError:  # one challenge
                pass
            except TypeError:  # solo player
                pass
            else:
                solve_challenges = await cls._fetch(session, config.api["base_link"] +
                                                    f'/solves/byteamid/{team_id}')
            if not solve_challenges:
                return []
            return [challenge['challenge']['id'] for challenge in solve_challenges]

class UpdateHelpers():
    @staticmethod
    async def main(bot: commands.Bot):
        for guild in bot.guilds:
            helper_role = discord.utils.get(
                guild.roles, name=config.roles['helper'])
            for helper in helper_role.members:
                solved_challenge_ids = await ScrapeChallenges.get_user_challenges(
                    helper.id)
                for ch_id in solved_challenge_ids:
                    db.update_helper_ch(helper.id, ch_id)

    @classmethod
    async def modify_helper_to_channel(cls, ticket_channel: discord.TextChannel, user_id: int, update: bool):
        helper = ticket_channel.guild.get_member(user_id)
        if helper is None:
            return
        if helper in ticket_channel.members:
            if update is False:
                await ticket_channel.set_permissions(helper, read_messages=False,
                                                     send_messages=False)
            else:
                raise exceptions.HelperSyncError(
                    "you can't be added to a channel you're already in!")
        elif update is True:
            await ticket_channel.set_permissions(helper, read_messages=True,
                                                 send_messages=True)

    @classmethod
    async def modify_helpers_to_channel(cls, bot: commands.Bot, member_id: discord.Member.id = None, choice: types.HelperSync = 'ADD'):
        for guild in bot.guilds:
            for channel_id in db.get_all_help_channels(guild.id):
                if (channel_ := guild.get_channel(channel_id)):
                    try:
                        helpers = db.get_helpers_from_title(
                            channel_.topic.split(" - ")[0])
                    except AttributeError:
                        continue

                    try:
                        helpers = json.loads(helpers[0])
                    except TypeError:
                        continue

                    if not helpers:
                        await UI.log_to_logs(
                            "Challenge not found", channel_)
                        log.debug(f"Challenge not found - {channel_}")
                        continue

                    if member_id:
                        if member_id in helpers:
                            await cls.modify_helper_to_channel(channel_, member_id, choice)
                        continue
                    for helper in helpers:
                        try:
                            if helper == db.get_user_id(channel_id):
                                continue
                        except ValueError:
                            pass
                        await cls.modify_helper_to_channel(channel_, helper, choice)
