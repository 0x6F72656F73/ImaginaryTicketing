"""
0 = nothing has happened
1 = bot has said 1 message
2 = channel will be ignored
"""

import asyncio
from datetime import timedelta, datetime
import json
from typing import Dict, List, NamedTuple, Union, Set
import logging

import discord
from discord.ext import commands
from environs import Env
import aiohttp
from trello import TrelloClient, List as TrelloList, Label

import cogs.helpers.views.action_views as action_views
import cogs.helpers.actions as actions
from utils import types, exceptions
from utils.options import Options
from utils.utility import Utility, UI, Challenge, TrelloChallenge
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
            await close.main()
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
        return {'apikey': env.str('IMAGINARYCTF_API_KEY')}

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

class UpdateTrello:
    def __init__(self, response_message: discord.Message):
        self.response_message = response_message
        try:
            self.response_embed = self.response_message.embeds[0]
        except AttributeError as e:
            raise AttributeError(
                "A progress embed needs to be sent as well") from e
        env = Env()
        env.read_env()
        self.client = TrelloClient(
            api_key=env.str('TRELLO_API_KEY'),
            api_secret=env.str('TRELLO_API_SECRET'),
        )
        all_boards = self.client.list_boards()
        self.current_month = next(
            filter(lambda board: board.name == "September", all_boards))
        self.all_categories = self.current_month.open_lists()
        self.built_challenges: List[TrelloChallenge] = []
        self.category_lengths: Dict[str, int] = {}

    async def setup(self):
        challenges = await ScrapeChallenges.fetch_challenges()
        for chall in challenges:
            chall['release_date'] = datetime.strptime(
                chall['release_date'], '%Y-%m-%dT%H:%M:%S.%f')
            self.built_challenges.append(TrelloChallenge.build(**chall))

        self.category_lengths = {cat: len(cat.list_cards())
                                 for cat in self.all_categories}
        try:
            self.response_embed.description += f"\nTotal number of challenges: {len(challenges)}\n"
        except TypeError:
            self.response_embed.description = f"Total number of challenges: {len(challenges)}\n"
        trello_all_challenges = self.current_month.open_cards()
        if len(challenges) != len(trello_all_challenges):
            built_chall_names = [
                chall.title for chall in self.built_challenges]
            cards_names = [
                card.name for card in trello_all_challenges]
            not_added = set(built_chall_names).difference(
                set(cards_names))
            self.response_embed.description += f"Total number of challenges not added: {len(not_added)}\n"
            for chall in not_added:
                self.response_embed.description += f"- {chall}\n"
        self.response_embed.description += "**Data:**\n"
        await self.response_message.edit(embed=self.response_embed)

    async def main(self):
        if not self.built_challenges:
            raise ValueError("Run setup first")
        for cat in self.all_categories:
            await self.add_challenges_to_category(cat)
        return self.response_embed

    def _delete_wrong_challenges(self):
        cards = self.current_month.all_cards()
        for card in cards:
            try:
                next(t for t in self.built_challenges if t.title == card.name)
            except StopIteration:
                card.delete()

    def _create_categories(self):
        should_categories = {chall.category for chall in self.built_challenges}
        current_categories = {
            category.name for category in self.all_categories}
        difference = should_categories.difference(current_categories)
        if difference:
            for category in difference:
                self.current_month.add_list(category)

    def _difficulty(self, points: int) -> Label:
        labels = self.current_month.get_labels()
        if points < 75:
            return (l for l in labels if l.name == "easy")
        if points < 125:
            return (l for l in labels if l.name == "easy/medium")
        if points < 150:
            return (l for l in labels if l.name == "medium")
        if points < 175:
            return (l for l in labels if l.name == "medium/hard")
        if points < 250:
            return (l for l in labels if l.name == "hard")
        return (l for l in labels if l.name == "extremely hard")

    @staticmethod
    def _completed(time: datetime):
        return datetime.now() > time

    async def add_challenges_to_category(self, category: TrelloList):
        category_challenges: Set[TrelloChallenge] = {
            chall for chall in self.built_challenges if chall.category == category.name}
        category_challenges = sorted(
            category_challenges, key=lambda c: c.release_date)

        for card in category.list_cards_iter():
            for ch in category_challenges.copy():
                if card.name == ch.title:
                    category_challenges.remove(ch)

        for ch in category_challenges:
            pts = self._difficulty(ch.points)
            card = category.add_card(ch.title, labels=pts,
                                     due=str(ch.release_date))
            if self._completed(ch.release_date):
                card.set_due_complete()
            self.response_embed.description += f" **added** {ch.title}\n"
            await self.response_message.edit(embed=self.response_embed)

    async def _categories_sorted(self) -> bool:
        lengths = [len(cat.list_cards()) for cat in self.all_categories]
        # lengths.index
        correct = sorted(lengths)
        print(lengths, correct)
        return correct == lengths

    def search(self, category):
        for cat, len_ in self.category_lengths.items():
            if cat == category:
                return self.category_lengths[cat]

    async def sort_categories(self):
        print(f"all categories: {self.all_categories}")
        print('------------')
        for cat in self.all_categories:
            print(cat, cat.pos)
        correct = dict(sorted(self.category_lengths.items(),
                              key=lambda x: x[1]))
        print(f"all category lengths: {self.category_lengths}")
        print('------------')
        print(f"correct category lengths: {correct}")
        print('------------')
        cor = list(correct.keys())
        for idx, (category, len_) in enumerate(self.category_lengths.items()):
            # cor = correct[category]
            a = cor.index(category)
            if idx == a:
                print(f'category {category} is in the correct position!')
                continue
            print(f'category {category} is in the wrong position!')
            b = cor[a]
            print(idx, a, b)
            cur_pos = category.pos
            for cat_len in correct.items():
                cat = cat_len[0]  # make diagram or sum, cuz its rlly confusing
                print(cat)
                if category == cat:
                    print(category.pos, cat.pos)
            break
            new_pos = next(cat.pos for cat in correct.items() if category ==)
            for x in cor:
                if x == category:
                    print(x)
            print(category, category.pos, len_, cor)
        for key in self.category_lengths.keys() & correct.keys():
            print(key, key.pos, self.category_lengths[key], correct[key])

        self.category_lengths = {cat: len(cat.list_cards())
                                 for cat in self.all_categories}
        await self._categories_sorted()
        for _ in range(len(self.category_lengths)):
            for idx, (cat, len_) in enumerate(self.category_lengths.items()):
                print(idx, cat, len_)
                a = self.search()
        try:
            next_cat = self.all_categories[idx + 1]
        except IndexError:
            continue
        if len_ > len(next_cat.list_cards()):
            cur_pos = cat.pos
            new_pos = self.all_categories[idx + 1].pos
            self.all_categories[idx + 1].set_pos(cur_pos)
            cat.set_pos(new_pos)
        for idx, (cat, pos) in enumerate(category_lengths.items()):
            print(idx, (cat, pos))
            if pos > any(category_lengths.values()):
                print(cat)
            # new_cat = next(
            # #     cat for cat in category_lengths.values() if cat[1] == [idx + 1])
            # # print(new_cat)
            # for idj, cat in enumerate(category_lengths.values()):
            #     print(cat, cat[1] == [idx + 1])
            # # new_cat = category_lengths.values()[1] == [idx + 1]
            # if (pos > category_lengths[idx + 1].pos):  # change to while
            #     print(category_lengths[idx + 1])
            #     # cur_pos = pos
            #     # new_pos = category_lengths[idx + 1].pos
            #     # category_lengths[idx + 1] = pos
        while (self._categories_sorted):
        for _ in range(len(self.all_categories)):
            for idx, cat in enumerate(self.all_categories):
                try:
                    next_cat = self.all_categories[idx + 1]
                except IndexError:
                    continue
                if len(cat.list_cards()) > len(next_cat.list_cards()):
                    cur_pos = cat.pos
                    new_pos = self.all_categories[idx + 1].pos
                    self.all_categories[idx + 1].set_pos(cur_pos)
                    cat.set_pos(new_pos)
