import json
import os
import asyncio
import collections
import logging
from typing import List, Set, Tuple, Union, Optional

import discord
from discord.ext import commands
from discord.utils import get
import humanize

import cogs.helpers.views.action_views as action_views
import config

from utils.database.db import DatabaseManager as db
from utils.utility import Utility, UI, Challenge
from utils.options import Options
from utils.background import ScrapeChallenges
from utils import exceptions, types

log = logging.getLogger(__name__)

class BaseActions:
    """Base class for all actions"""

    def __init__(self, guild: discord.Guild, user: Union[discord.User, discord.ClientUser],
                 channel: discord.TextChannel, background: bool = False):
        self.guild = guild
        if background:
            self.user = user.user
            self.user_id = self.user.id
        else:
            self.user = user
            self.user_id = self.user.id
        self.channel = channel
        self.channel_id = channel.id

    async def _log_to_channel(self, msg: str, *args, **kwargs) -> None:
        """Shorthand method to log messages

        Parameters
        ----------
        msg : `str`
            message to log
        """
        await UI.log_to_logs(msg, self.channel, self.user, *args, **kwargs)

    async def _move_channel(self, category_name) -> discord.CategoryChannel:
        """Fetches or creates the category

        Parameters
        ----------
        category_name : `str`
            The category\n

        Returns
        -------
        `discord.CategoryChannel` : The category
        """
        category = get(self.guild.categories, name=category_name)
        if category is None:
            new_category = await self.guild.create_category(name=category_name)
            category = self.guild.get_channel(new_category.id)
        return category

    async def _ticket_information(self):
        number = db.get_number_previous(self.channel_id)
        current_type = db.get_ticket_type(self.channel_id)
        try:
            user_id = db.get_user_id(self.channel_id)
        except ValueError as e:
            return await self.channel.send(e.args[0])
        user = self.guild.get_member(user_id)

        return number, current_type, user_id, user
class CreateTicket(BaseActions):
    def __init__(self, bot: commands.Bot, ticket_type: types.TicketType, interaction: Optional[discord.Interaction], *args, **kwargs):
        self.bot = bot
        self.ticket_type = ticket_type
        if interaction:
            self.send_pm = lambda m: interaction.response.send_message(
                m, ephemeral=True)
        else:
            self.send_pm = lambda m: self.user.send(m)

        self.ticket_channel: discord.TextChannel = None
        self._args = [interaction, args, kwargs]
        super().__init__(*args, **kwargs)

    async def _setup(self):
        admin = get(self.guild.roles, name=config.roles['admin'])
        member = self.guild.get_member(self.user_id)
        if admin not in member.roles:
            await self._maximum_tickets()

        self.ticket_channel = await self._create_ticket_channel()

        await self.send_pm(f'You can view your ticket at {self.ticket_channel.mention}')

    async def _maximum_tickets(self):
        try:
            n_tickets = db.get_user_open_tickets(
                self.ticket_type, self.user_id)
        except ValueError as e:
            return await self.channel.send(e.args[0])
        limit = Options.limit(self.ticket_type)
        if n_tickets >= limit:
            await self.send_pm(f"You have reached the maximum limit ({n_tickets}/{limit}) for this ticket type")
            raise exceptions.MaxUserTicketError

    async def _create_ticket_channel(self) -> discord.TextChannel:
        number = db.get_number_new(self.ticket_type, self.guild.id)
        channel_name = Options.name_open(
            self.ticket_type, number, self.user)
        cat = Options.full_category_name(self.ticket_type)
        category = get(self.guild.categories, name=cat)
        if category is None:
            new_category = await self.guild.create_category(name=cat)
            category = self.guild.get_channel(new_category.id)
        if len(category.channels) > 49:
            await self.send_pm("There are over 50 channels in the selected category. Please contact a server admin.")
            raise exceptions.MaxChannelTicketError

        admin = get(self.guild.roles, name=config.roles['admin'])
        bots = get(self.guild.roles, name=config.roles['bot'])
        muted = get(self.guild.roles, name=config.roles['muted'])
        quarantine = get(self.guild.roles, name=config.roles['quarantine'])
        member = self.guild.get_member(self.user_id)

        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            admin: discord.PermissionOverwrite(
                read_messages=True),
            bots: discord.PermissionOverwrite(read_messages=True),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            muted: discord.PermissionOverwrite(
                create_instant_invite=False, send_messages=False),
            quarantine: discord.PermissionOverwrite(
                view_channel=False, create_instant_invite=False, send_messages=False)
        }

        return await category.create_text_channel(channel_name, overwrites=overwrites)

    async def main(self) -> discord.TextChannel:
        """Creates a ticket"""

        await self._setup()

        if self.ticket_type == "help":
            welcome_message = f'Welcome <@{self.user_id}>'
            await self.ticket_channel.send(welcome_message)

        status = "open"
        check = "2"
        db.create_ticket(self.ticket_channel.id, str(
            self.ticket_channel), self.guild.id, self.user_id, self.ticket_type, status, check)

        avail_mods = get(
            self.guild.roles, name=config.roles['ticket ping'])
        if self.ticket_type == "help":
            helper = CreateTicketHelper(
                self.ticket_channel, self.bot, self.ticket_type, self._args[0], *self._args[1], **self._args[2])
            ch_authors = await helper.challenge_selection()
            ch_authors = set(filter(lambda v: v is not None, ch_authors))
            if len(ch_authors) == 0:
                author_mentions = ''
            else:
                author_mentions = ', ' + ', '.join(
                    [author.mention for author in ch_authors])
            welcome_message = f'A new ticket has been created {avail_mods.mention} {author_mentions}'
        elif self.ticket_type == "submit":
            welcome_message = f'Welcome <@{self.user_id}>'
        else:
            welcome_message = f'Welcome <@{self.user_id}>\nA new ticket has been created {avail_mods.mention}\n'
        message = Options.message(self.ticket_type, avail_mods)

        embed = UI.Embed(description=message)
        ticket_channel_message = await self.ticket_channel.send(welcome_message, embed=embed, view=action_views.CloseView())

        await ticket_channel_message.pin()
        await self.ticket_channel.purge(limit=1)

        db.update_check("0", self.ticket_channel.id)

        await self._log_to_channel("Created ticket")
        log.info(
            f"[CREATED] {self.ticket_channel} by {self.user} (ID: {self.channel_id})")
        return self.ticket_channel
class CreateTicketHelper(CreateTicket):
    def __init__(self, ticket_channel: discord.TextChannel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket_channel = ticket_channel

    @staticmethod
    def fake_challenges(num):
        category_list = ["Crypto", "Web", "Pwn", "Rev", "Misc"]
        categories = {}
        for idx, category in enumerate(category_list):  # whats this for..
            categories[idx] = category
        list_categories = list(categories.values())
        return [Challenge(
            i, f"chall{i}", f"author{i}", list_categories[i % len(categories)], i % 3 == 0) for i in range(num)]

    async def _ask_for_challenge(self, challenges: List[Challenge]):
        challenge_options = [discord.SelectOption(
            label=(challenge.title[:23] + '..') if len(challenge.title) > 25 else challenge.title, value=f"{challenge.id}") for challenge in challenges]

        while True:
            view = action_views.ChallengeView(author=self.user, custom_id=f"ticketing:challenge_request-{os.urandom(16).hex()}", options=challenge_options,
                                              placeholder="Please choose a challenge")
            select_messages = await self.ticket_channel.send("Please select which challenge you need help with", view=view)
            await view.wait()
            if view.children[0]._selected_values:
                break
            await select_messages.delete()

        selected_challenge = [
            ch for ch in challenges if ch.id == int(view.children[0]._selected_values[0])][0]
        return selected_challenge

    async def _ask_for_category(self, challenges: List[Challenge]) -> List[Challenge]:
        categories = {ch.category for ch in challenges}
        category_options = [discord.SelectOption(
            label=cat, value=cat) for cat in categories]
        while True:
            view = action_views.ChallengeView(author=self.user, custom_id=f"ticketing:category_request-{os.urandom(16).hex()}", options=category_options,
                                              placeholder="Please choose a category")
            select_messages = await self.ticket_channel.send("Please select which category you need help with", view=view)
            await view.wait()
            if view.children[0]._selected_values:
                break
            await select_messages.delete()
        category_challenges = [
            ch for ch in challenges if ch.category == view.children[0]._selected_values[0]]
        return category_challenges

    async def _add_author_and_helpers(self, selected_challenge: Challenge) -> Set[Union[discord.Member, None]]:
        ch_authors = set()
        if len(authors := selected_challenge.author.split('/')) > 1:
            for author in authors:
                author = await UtilityActions._add_member(author, selected_challenge.title, self.guild, self.ticket_channel)
                ch_authors.add(author)
        else:
            author = await UtilityActions._add_member(selected_challenge.author, selected_challenge.title, self.guild, self.ticket_channel)
            ch_authors.add(author)

        if len(helpers := json.loads(selected_challenge.helper_id_list)):
            for helper in helpers:
                try:
                    if db.get_helper_status(helper):
                        await UtilityActions._add_member(int(helper), selected_challenge.title, self.guild, self.ticket_channel)
                except ValueError:
                    pass
        return ch_authors  # Returns the author to be pinged on ticket creation

    async def challenge_selection(self) -> Set[Union[discord.Member, None]]:
        # challenges = CreateTicketHelper.fake_challenges(21)
        user_solved_challenges = await ScrapeChallenges.get_user_challenges(
            self.user_id)
        challenges = [Challenge(*list(challenge))
                      for challenge in db.get_all_challenges() if not Challenge(*list(challenge)).id in user_solved_challenges]

        if len(challenges) < 1:
            await self.ticket_channel.send("There are no released challenges or you have solved all the currently released challenges")
            return

        member = self.guild.get_member(self.user_id)
        await self.ticket_channel.set_permissions(member, read_messages=True,
                                                  send_messages=False)

        if len(challenges) <= 25:
            selected_challenge = await self._ask_for_challenge(list(reversed(challenges)))
        else:
            selected_challenge = await self._ask_for_challenge(await self._ask_for_category(challenges))

        await self.ticket_channel.edit(topic=f"{selected_challenge.title} - {selected_challenge.author}")

        await self.ticket_channel.set_permissions(member, read_messages=True,
                                                  send_messages=None)
        user_message = await self.ticket_channel.send("What have your tried so far?")

        def user_response_check(message):
            return message.channel == self.ticket_channel and message.author == self.user
        await self.bot.wait_for('message', check=user_response_check)
        await user_message.delete()

        return await self._add_author_and_helpers(selected_challenge)

class UtilityActions:
    @staticmethod
    async def add(channel: discord.TextChannel, member: discord.Member):
        """adds a member to a ticket(try adding roles(typehint optional))

        Parameters
        ----------
        member : `discord.Member`
            member to be added\n
        """
        await channel.set_permissions(member, read_messages=True, send_messages=True)

        embed = UI.Embed(description=f"{member.mention} was added")
        await channel.send(embed=embed)

    @staticmethod
    async def remove(channel: discord.TextChannel, member: discord.Member):
        """remove a member to a ticket(try adding roles(typehint optional))

        Parameters
        ----------
        member : `discord.Member`
            member to be removed\n
        """
        await channel.set_permissions(member, read_messages=False, send_messages=False)
        embed = UI.Embed(description=f"{member.mention} was removed")
        await channel.send(embed=embed)

    # change to member after website
    @staticmethod
    async def _add_member(member_identifier: Union[str, int], challenge_title: str, guild: discord.Guild, ticket_channel: discord.TextChannel) -> Union[discord.Member, None]:
        # change to get_member after website
        if isinstance(member_identifier, str):
            author = guild.get_member_named(member_identifier)
        else:
            author = guild.get_member(member_identifier)
        try:
            await ticket_channel.set_permissions(author, read_messages=True,
                                                 send_messages=True)
        except discord.InvalidArgument:
            log.info(
                f"Member {member_identifier} for challenge {challenge_title} does not exist.")
        return author

class CloseTicket(BaseActions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

    async def close_stats_helper(self, channel: discord.TextChannel) -> Tuple[str, str]:
        """gets all the users in a channel

        Parameters
        ----------
        channel : `discord.TextChannel`
            channel to get users from\n

        Returns
        -------
        `str`: joined list of users to count reference from channel,
        `str`: time the channel was open
        """
        users = [msg.author.name async for msg in channel.history(limit=2000).filter(lambda message: not message.author.bot)]

        message_distribution = collections.Counter(users)
        total_messages = sum(message_distribution.values())
        if len(message_distribution) > 0:
            channel_users = []
            for member, count in message_distribution.most_common():
                channel_users.append(
                    f"{self.guild.get_member_named(member).mention} ({count/total_messages:.0%})")
            channel_users.append(f'total: {len(users)}')
            channel_users = '\n'.join(channel_users)
        else:
            channel_users = 'No messages'
        old = channel.created_at

        now = discord.utils.utcnow()
        duration = now - old
        time_open = humanize.precisedelta(
            duration, format="%0.0f", minimum_unit="minutes"
            if duration.total_seconds() > 60 else "seconds")

        return channel_users, time_open

    async def main(self, inactivity=False):
        """closes a ticket"""
        try:
            current_status = db.get_status(self.channel_id)
        except ValueError as e:
            return await self.channel.send(e.args[0])

        if current_status == "closed":
            await self.channel.send("Channel is already closed")
            return

        close_stats_embed = UI.Embed()
        close_stats_embed.set_author(
            name=f"{self.user}", icon_url=f"{self.user.avatar.url}")
        embed_message = await self.channel.send(embed=close_stats_embed)

        t_number, t_current_type, t_user_id, t_user = await self._ticket_information()

        member = self.guild.get_member(t_user_id)
        await self.channel.set_permissions(member, read_messages=None)

        category = await self._move_channel("Closed Tickets")

        closed_name = Options.name_close(
            t_current_type, count=t_number, user=t_user)
        await self.channel.edit(name=closed_name, category=category)

        db.update_ticket_name(closed_name, self.channel_id)

        channel_log_category = get(
            self.guild.categories, name=config.logs["category"])
        if channel_log_category is None:
            await self.channel.send("logs category does not exist")
            return
        channel_log = get(
            self.guild.text_channels, category=channel_log_category, name=config.logs["name"])
        if channel_log is None:
            await self.channel.send(f"{config.logs['name']} channel does not exist in category logs")
            return

        transcript_message, transcript_file = await Utility.transcript(self.channel, channel_log)
        if transcript_message:
            close_stats_embed.add_field(name="transcript",
                                        value=f"[transcript url]({config.transcript['domain']}/transcript?link={transcript_message.attachments[0].url} \"oreos taste good dont they\") ")
        else:
            close_stats_embed.add_field(
                name="transcript", value="transcript could not be sent to DMs")
        await embed_message.edit(embed=close_stats_embed)

        channel_users, time_open = await self.close_stats_helper(self.channel)

        close_stats_embed.add_field(
            name="message distribution", value=f"{channel_users}")
        close_stats_embed.add_field(
            name="time open", value=f"{time_open}")
        if inactivity:
            message = "This ticket was automatically closed due to inactivity."
            await t_user.send(message, embed=close_stats_embed, file=transcript_file)
        else:
            await t_user.send(embed=close_stats_embed, file=transcript_file)
        await embed_message.edit(embed=close_stats_embed, view=action_views.ReopenDeleteView())

        status = "closed"
        db.update_status(status, self.channel_id,)

        channel_log = get(
            self.guild.text_channels, name=config.logs['name'])
        close_stats_embed.title = "Closed ticket"
        close_stats_embed.set_footer(text=f"{self.channel}")
        await channel_log.send(embed=close_stats_embed)
        log.info(
            f"[CLOSED] {self.channel} by {self.user} (ID: {self.channel_id})")

class ReopenTicket(BaseActions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def main(self):
        """reopens a ticket"""
        try:
            test_status = db.get_status(self.channel_id)
        except ValueError as e:
            return await self.channel.send(e.args[0])

        if test_status == "open":
            await self.channel.send("Channel is already open")
            return

        t_number, t_current_type, t_user_id, t_user = await self._ticket_information()

        cat = Options.full_category_name(t_current_type)
        category = get(self.guild.categories, name=cat)
        if category is None:
            new_category = await self.guild.create_category(name=cat)
            category = self.guild.get_channel(new_category.id)

        member = self.guild.get_member(t_user_id)
        await self.channel.set_permissions(member, read_messages=True)

        reopened = Options.name_open(
            t_current_type, count=t_number, user=t_user)
        await self.channel.edit(name=reopened, category=category)
        db.update_ticket_name(reopened, self.channel_id)

        status = "open"
        db.update_status(status, self.channel_id)
        reopened_embed = UI.Embed(
            description="Ticket was re-opened")
        reopened_embed.set_author(
            name=f"{self.user}", icon_url=f"{self.user.avatar.url}")
        await self.channel.send(embed=reopened_embed, view=action_views.CloseView())

        await self._log_to_channel("Re-Opened ticket")
        log.info(
            f"[RE-OPENED] {self.channel} by {self.user} (ID: {self.channel_id})")

class DeleteTicket(BaseActions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def main(self):
        """deletes a ticket"""
        try:
            db.get_channel_name(self.channel_id)
        except ValueError as e:
            return await self.channel.send(e.args[0])

        embed = UI.Embed(
            title="Deleting ticket",
            description="5 seconds left")
        await self.channel.send(embed=embed)
        await asyncio.sleep(5)
        await self.channel.delete()

        db.move_ticket_to_archive(self.channel_id)

        db.delete_ticket(self.channel_id)

        await self._log_to_channel("Deleted ticket")
        log.info(
            f"[DELETED] {self.channel} by {self.user} (ID: {self.channel_id})")
