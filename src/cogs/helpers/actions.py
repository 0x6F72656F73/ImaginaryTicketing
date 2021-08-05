import os
import asyncio
from collections import Counter
import logging
from typing import List, Tuple, Union, Optional

import discord
from discord.ext import commands
from discord.utils import get
from humanize import precisedelta

import cogs.helpers.views.action_views as action_views
from utils.others import Others
from utils.options import Options
import utils.exceptions as exceptions
from utils.database.db import DatabaseManager as db
from utils.background import ScrapeChallenges
import config

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
        """Logs a message to channel ticket-log

        Parameters
        ----------
        msg : `str`
            message to log
        """
        channel_log = get(
            self.guild.text_channels, name="ticket-log")
        logembed = await Others.log_embed(
            msg, self.user, self.user.avatar.url, self.channel, *args, **kwargs)
        await channel_log.send(embed=logembed)

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

    def _ticket_information(self):
        number = db.get_number_previous(self.channel_id)
        current_type = db.get_ticket_type(self.channel_id)
        user_id = db.get_user_id(self.channel_id)
        user = self.guild.get_member(user_id)

        return number, current_type, user_id, user
class CreateTicket(BaseActions):
    def __init__(self, bot: commands.Bot, ticket_type: str, interaction: Optional[discord.Interaction], *args, **kwargs):
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
        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        member = self.guild.get_member(self.user_id)
        if admin not in member.roles:
            await self._maximum_tickets()

        self.ticket_channel = await self._create_ticket_channel()

        await self.send_pm(f'You can view your ticket at {self.ticket_channel.mention}')

    async def _maximum_tickets(self):
        n_tickets = db._raw_select(
            "SELECT count(1) FROM (SELECT * FROM requests WHERE ticket_type=$1 and user_id=$2)", (self.ticket_type, self.user_id,), fetch_one=True)
        current = n_tickets[0]
        limit = Options.limit(self.ticket_type)
        if current >= limit:
            await self.send_pm(f"You have reached the maximum limit ({current}/{limit}) for this ticket type")
            raise exceptions.MaxUserTicketError

    async def _create_ticket_channel(self) -> discord.TextChannel:
        number = db.get_number_new(self.ticket_type)
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

        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        bots = get(self.guild.roles, name=config.BOTS_ROLE)
        member = self.guild.get_member(self.user_id)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            bots: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            admin: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }

        return await category.create_text_channel(channel_name, overwrites=overwrites)

    async def main(self) -> discord.TextChannel:
        """Creates a ticket"""

        await self._setup()

        if self.ticket_type == "help":
            welcome_message = f'Welcome <@{self.user_id}>'
            await self.ticket_channel.send(welcome_message)

        status = "open"
        checked = "0"
        db._raw_insert("INSERT INTO requests (channel_id, channel_name, guild_id, user_id, ticket_type, status, checked) VALUES ($1,$2,$3,$4,$5,$6,$8 )", (
            self.ticket_channel.id, str(self.ticket_channel), self.guild.id, self.user_id, self.ticket_type, status, checked))
        if self.ticket_type == "help":
            helper = _CreateTicketHelper(
                self.ticket_channel, self.bot, self.ticket_type, self._args[0], *self._args[1], **self._args[2])
            await helper.challenge_selection()

        avail_mods = get(
            self.guild.roles, name=config.TICKET_PING_ROLE)
        if self.ticket_type == "help":
            welcome_message = f'A new ticket has been created {avail_mods.mention}'
        elif self.ticket_type == "submit":
            welcome_message = f'Welcome <@{self.user_id}>'
        else:
            welcome_message = f'Welcome <@{self.user_id}>\nA new ticket has been created {avail_mods.mention}\n'
        message = Options.message(self.ticket_type, avail_mods)

        embed = Others.Embed(description=message)
        ticket_channel_message = await self.ticket_channel.send(welcome_message, embed=embed, view=action_views.CloseView())

        await ticket_channel_message.pin()
        await self.ticket_channel.purge(limit=1)

        await self._log_to_channel("Created ticket")
        log.info(
            f"[CREATED] {self.ticket_channel} by {self.user} (ID: {self.channel_id})")
        return self.ticket_channel
class _CreateTicketHelper(CreateTicket):
    def __init__(self, ticket_channel: discord.TextChannel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ticket_channel = ticket_channel

    def _fake_challenges(self, num):
        category_list = ["Crypto", "Web", "Pwn", "Rev", "Misc"]
        categories = {}
        for idx, category in enumerate(category_list):
            categories[idx] = category
        list_categories = list(categories.values())
        return [Others.Challenge(
            i, f"chall{i}", f"author{i}", list_categories[i % len(categories)], i % 3 == 0) for i in range(num)]

    class ChallengeSelect(discord.ui.Select['ChallengeView']):
        def __init__(self, custom_id: str, options: List[discord.SelectOption], placeholder: str):
            super().__init__(custom_id=custom_id,
                             placeholder=placeholder, min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            await interaction.message.delete()
            view = self.view  # pylint: disable=maybe-no-member
            view.stop()

    class ChallengeView(discord.ui.View):
        def __init__(self, author: discord.Member, custom_id: str, options: List[discord.SelectOption], placeholder: str, timeout: float = 300, **kwargs):
            super().__init__(timeout=timeout, **kwargs)
            self.add_item(_CreateTicketHelper.ChallengeSelect(
                custom_id, options, placeholder))
            self.author = author

        async def interaction_check(self, interaction: discord.Interaction):
            if interaction.user == self.author:
                return True
            await interaction.response.send_message("You're not allowed to choose", ephemeral=True)
            return False

    async def _ask_for_challenge(self, challenges: List[Others.Challenge]):
        challenge_options = [discord.SelectOption(
            label=(challenge.title[:23] + '..') if len(challenge.title) > 25 else challenge.title, value=f"{challenge.id_}") for challenge in challenges]

        while True:
            view = self.ChallengeView(author=self.user, custom_id=f"ticketing:challenge_request-{os.urandom(16).hex()}", options=challenge_options,
                                      placeholder="Please choose a challenge")
            select_messages = await self.ticket_channel.send("Please select which challenge you need help with", view=view)
            await view.wait()
            if view.children[0]._selected_values:
                break
            await select_messages.delete()

        selected_challenge = [
            ch for ch in challenges if ch.id_ == int(view.children[0]._selected_values[0])][0]
        return selected_challenge

    async def _ask_for_category(self, challenges: List[Others.Challenge]) -> List[Others.Challenge]:
        categories = {ch.category for ch in challenges}
        category_options = [discord.SelectOption(
            label=cat, value=cat) for cat in categories]
        while True:
            view = self.ChallengeView(author=self.user, custom_id=f"ticketing:category_request-{os.urandom(16).hex()}", options=category_options,
                                      placeholder="Please choose a category")
            select_messages = await self.ticket_channel.send("Please select which category you need help with", view=view)
            await view.wait()
            if view.children[0]._selected_values:
                break
            await select_messages.delete()
        category_challenges = [
            ch for ch in challenges if ch.category == view.children[0]._selected_values[0]]
        return category_challenges

    async def add_user(self, user: discord.User):  # change to member after website
        # change to get_member after website
        author = self.guild.get_member_named(user)
        if author is None:
            return
        await self.ticket_channel.set_permissions(author, read_messages=True,
                                                  send_messages=True)

    async def challenge_selection(self):
        # challenges = self._fake_challenges(21)
        user_solved_challenges = ScrapeChallenges.get_user_challenges(
            self.user_id)
        challenges = [Others.Challenge(*list(challenge))
                      for challenge in db.get_all_challenges() if not Others.Challenge(*list(challenge)).id_ in user_solved_challenges]

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
                                                  send_messages=True)
        user_message = await self.ticket_channel.send("What have your tried so far?")

        def user_response_check(message):
            return message.channel == self.ticket_channel and message.author == self.user
        await self.bot.wait_for('message', check=user_response_check)
        await user_message.delete()
        await self.add_user(selected_challenge.author)
class Utility:
    @staticmethod
    async def add(channel: discord.TextChannel, member: discord.Member):
        """adds a member to a ticket(try adding roles(typehint optional))

        Parameters
        ----------
        member : `discord.Member`
            member to be added\n
        """
        await channel.set_permissions(member, read_messages=True, send_messages=True)

        embed = Others.Embed(description=f"{member.mention} was added")
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
        embed = Others.Embed(description=f"{member.mention} was removed")
        await channel.send(embed=embed)


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

        message_distribution = Counter(users)
        total_messages = sum(message_distribution.values())
        channel_users = '\n'.join(
            [f"{self.guild.get_member_named(member).mention} ({count/total_messages:.0%})" for member, count in message_distribution.most_common()]) if len(message_distribution) > 0 else 'No messages'
        old = channel.created_at

        now = discord.utils.utcnow()
        duration = now - old
        if duration.total_seconds() < 60:
            time_open = precisedelta(
                duration, format="%0.0f", minimum_unit="seconds")
        else:
            time_open = precisedelta(
                duration, format="%0.0f", minimum_unit="minutes")
        return channel_users, time_open

    async def main(self):
        """closes a ticket"""
        current_status = db.get_status(self.channel_id)
        if current_status == "closed":
            await self.channel.send("Channel is already closed")
            return

        close_stats_embed = Others.Embed()
        close_stats_embed.set_author(
            name=f"{self.user}", icon_url=f"{self.user.avatar.url}")
        embed_message = await self.channel.send(embed=close_stats_embed)

        member = self.guild.get_member(self.user_id)
        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=None, send_messages=None),
            admin: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }
        category = await self._move_channel("Closed Tickets")

        try:
            await self.channel.edit(category=category, overwrites=overwrites)
        except AttributeError:
            pass

        t_number, t_current_type, _, t_user = self._ticket_information()

        closed_name = Options.name_close(
            t_current_type, count=t_number, user=t_user)
        await self.channel.edit(name=closed_name)

        db._raw_update(
            "UPDATE requests SET channel_name = $1 WHERE channel_id = $2", (closed_name, self.channel_id,))

        channel_log_category = get(
            self.guild.categories, name=config.LOG_CHANNEL_CATEGORY)
        if channel_log_category is None:
            await self.channel.send("logs category does not exist")
            return
        channel_log = get(
            self.guild.text_channels, category=channel_log_category, name="ticket-log")
        if channel_log is None:
            await self.channel.send("ticket-log channel does not exist in category logs")
            return

        transcript_message, transcript_file = await Others.transcript(self.channel, channel_log)
        if transcript_message:
            close_stats_embed.add_field(name="transcript",
                                        value=f"[transcript url]({config.TRANSCRIPT_DOMAIN}/direct?link={transcript_message.attachments[0].url} \"oreos taste good dont they\") ")
        else:
            close_stats_embed.add_field(
                name="transcript", value="transcript could not be sent to DMs")
        await embed_message.edit(embed=close_stats_embed)

        channel_users, time_open = await self.close_stats_helper(self.channel)

        close_stats_embed.add_field(
            name="message distribution", value=f"{channel_users}")
        close_stats_embed.add_field(
            name="time open", value=f"{time_open}")

        await t_user.send(embed=close_stats_embed, file=transcript_file)
        await embed_message.edit(embed=close_stats_embed, view=action_views.ReopenDeleteView())

        status = "closed"
        db.update_status(status, self.channel_id,)

        channel_log = get(
            self.guild.text_channels, name="ticket-log")
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
            if test_status == "open":
                await self.channel.send("Channel is already open")
                return
        except:
            return

        t_number, t_current_type, t_user_id, t_user = self._ticket_information()

        if None in (t_number, t_current_type, t_user_id, t_user):
            await self.channel.send("Channel is not a ticket")
            return

        cat = Options.full_category_name(t_current_type)
        category = get(self.guild.categories, name=cat)
        if category is None:
            new_category = await self.guild.create_category(name=cat)
            category = self.guild.get_channel(new_category.id)

        member = self.guild.get_member(t_user_id)
        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            admin: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }
        await self.channel.edit(overwrites=overwrites, category=category)

        status = "open"
        db.update_status(status, self.channel_id)
        reopened_embed = Others.Embed(
            description="Ticket was re-opened")
        reopened_embed.set_author(
            name=f"{self.user}", icon_url=f"{self.user.avatar.url}")
        await self.channel.send(embed=reopened_embed, view=action_views.CloseView())

        reopened = Options.name_open(
            t_current_type, count=t_number, user=t_user)
        await self.channel.edit(name=reopened)
        db._raw_update(
            "UPDATE requests set channel_name = $1 WHERE channel_id = $2", (reopened, self.channel_id,))

        await self._log_to_channel("Re-Opened ticket")
        log.info(
            f"[RE-OPENED] {self.channel} by {self.user} (ID: {self.channel_id})")

class DeleteTicket(BaseActions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def main(self):
        """deletes a ticket"""
        db_channel_name = db.get_channel_name(self.channel_id)
        if db_channel_name is None:
            await self.channel.send("Channel is not a ticket")
            return

        embed = Others.Embed(
            title="Deleting ticket",
            description="5 seconds left")
        await self.channel.send(embed=embed)
        await asyncio.sleep(5)
        await self.channel.delete()

        db._raw_insert(
            "INSERT INTO archive SELECT * FROM requests WHERE channel_id= $1", (self.channel_id,))

        db._raw_delete(
            "DELETE FROM requests WHERE channel_id = $1", (self.channel_id,))

        await self._log_to_channel("Deleted ticket")
        log.info(
            f"[DELETED] {self.channel} by {self.user} (ID: {self.channel_id})")
