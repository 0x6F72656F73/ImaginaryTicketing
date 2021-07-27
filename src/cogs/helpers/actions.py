import datetime
import asyncio
import textwrap
import logging
from typing import List, Tuple, Union

import discord
from discord import Embed
from discord.utils import get
from discord.ext import commands
# from discord.ext.forms import NaiveForm, ReactionForm

# from discord_slash import ComponentContext
# from discord_slash.utils.manage_components import create_button, create_select, create_select_option, create_actionrow, wait_for_component
# from discord_slash.model import ButtonStyle

import cogs.helpers.views.action_views as action_views
from utils.others import Others
from utils.options import Options
from utils.database.db import DatabaseManager as db
import config

log = logging.getLogger(__name__)

class BaseActions(commands.Cog):
    """handles all reactions"""

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

    async def _log_to_channel(self, msg: str):
        """Logs a message to channel ticket-log

        Parameters
        ----------
        msg : `str`
            message to log
        """
        channel_log = get(
            self.guild.text_channels, name="ticket-log")
        logembed = await Others.log_embed(
            msg, self.user, self.user.avatar.url, self.channel)
        await channel_log.send(embed=logembed)

    async def _move_channel(self, category_name):
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
    def __init__(self, type_: str, *args, **kwargs):
        self.type_ = type_
        super().__init__(*args, *kwargs)

    async def main(self) -> discord.TextChannel:
        """Creates a ticket"""
        async def maximum_tickets():
            n_tickets = db._raw_select(
                "SELECT count(1) FROM (SELECT * FROM requests WHERE ticket_type=$1 and user_id=$2)", (ticket_type, self.user_id,), fetch_one=True)
            current = n_tickets[0]
            limit = Options.limit(ticket_type)
            if current >= limit:
                emby = await Others.make_embed(
                    0x00FFFF, f"You have reached the maximum limit ({current}/{limit}) for this ticket type")
                await self.user.send(embed=emby)
                return

        async def create_ticket_channel() -> discord.TextChannel:
            number = db.get_number_new(ticket_type)
            channel_name = Options.name_open(ticket_type, number, self.user)
            cat = Options.full_category_name(ticket_type)
            category = get(self.guild.categories, name=cat)
            if category is None:
                new_category = await self.guild.create_category(name=cat)
                category = self.guild.get_channel(new_category.id)

            overwrites = {
                self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                # add trusted bots role
                member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                admin: discord.PermissionOverwrite(
                    read_messages=True, send_messages=True)
            }

            return await category.create_text_channel(channel_name, overwrites=overwrites)

        # async def get_challenge():
            # async def choose_challenge(challenges: List[Others.Challenge]):
            #     options = [create_select_option(
            #         label=textwrap.shorten(challenge.title, 25, placeholder='...'), value=f"{challenge.id_}") for challenge in challenges]
            #     select = create_select(
            #         options=options,
            #         placeholder="Please choose a challenge",
            #         max_values=1)

            #     action_row = create_actionrow(select)
            #     await ctx.channel.send(components=[action_row], content="challenge selection")

            #     select_ctx: ComponentContext = await wait_for_component(self.client, components=action_row)
            #     await select_ctx.defer(edit_origin=True)
            #     selected_chall = [
            #         chall for chall in challenges if chall.id_ == int(select_ctx.selected_options[0])][0]
            #     await ticket_channel.edit(topic=f"this ticket is about {selected_chall}")
            #     await select_ctx.origin_message.delete()

            # async def choose_category(categories) -> List[Others.Challenge]:
            #     category_options = [create_select_option(
            #         label=category, value=f"{idx}") for idx, category in categories.items()]
            #     select = create_select(
            #         options=category_options,
            #         placeholder="Please choose a category",
            #         max_values=1)

            #     action_row = create_actionrow(select)
            #     await ctx.channel.send(components=[action_row], content="category selection")

            #     select_ctx: ComponentContext = await wait_for_component(self.client, components=action_row)
            #     await select_ctx.defer(edit_origin=True)
            #     selected_category = [
            #         chall.category for chall in challenges if chall.id_ == int(select_ctx.selected_options[0])][0]
            #     await select_ctx.origin_message.delete()
            #     category_challenges = [
            #         chall for chall in challenges if chall.category == selected_category]
            #     return category_challenges

            # def fake_challenges(num, categories):
            #     list_categories = list(categories)
            #     return [Others.Challenge(
            #         i, f"author{i}", f"chall{i}", list_categories[i % len(categories)], i % 3 == 0) for i in range(num)]

            # categories = ["Crypto", "Web", "Pwn", "Rev", "Misc"]
            # challenges = [(i, f"chall{i}", categories[i % len(
            #     categories)], i % 3 == 0) for i in range(30)]
            # categories = {}
            # for idx, chall in enumerate(challenges):
            #     if chall[2] not in categories.values():
            #         categories[idx] = chall[2]

            # challenges = fake_challenges(60, categories)
            # challenges = [Others.Challenge(*list(challenge))
            #               for challenge in db.get_all_challenges()]

            # print(f"{challenges=}")

            # if len(challenges) < 1:
            #     pass  # no challenges
            # elif len(challenges) < 25:
            #     await choose_challenge(challenges)
            # else:
            #     await choose_challenge(await choose_category(categories))

        # this loop can be deleted since reaction limits, and so does slash commands
        if self.type_ not in {'help', 'submit', 'misc'}:
            await self.channel.send("possible ticket types are help, submit, and misc")
            return
        else:
            ticket_type = self.type_

        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        member = self.guild.get_member(self.user_id)
        if admin not in member.roles:
            await maximum_tickets()

        ticket_channel = await create_ticket_channel()
        ticket_channel_id = ticket_channel.id

        status = "open"
        checked = "0"
        db._raw_insert("INSERT INTO requests (channel_id, channel_name, guild_id, user_id, ticket_type, status, checked) VALUES ($1,$2,$3,$4,$5,$6,$8 )", (
            ticket_channel_id, str(ticket_channel), self.guild.id, self.user_id, ticket_type, status, checked))
        # if ticket_type == "help":
        #     await get_challenge()

        avail_mods = get(
            self.guild.roles, name=config.TICKET_PING_ROLE)
        if not ticket_type == "submit":
            welcome_message = f'Welcome <@{self.user_id}>,\nA new ticket has been opened {avail_mods.mention}\n\n'
        else:
            welcome_message = f'Welcome <@{self.user_id}>\n\n'
        message = Options.message(ticket_type, avail_mods)

        embed = await Others.make_embed(0x5dc169, message)

        ticket_channel_message = await ticket_channel.send(welcome_message, embed=embed, view=action_views.CloseView())

        await ticket_channel_message.pin()
        await ticket_channel.purge(limit=1)

        if ticket_type == "help":
            await ticket_channel.send("What have your tried so far?")

        await self._log_to_channel("Created ticket")
        log.info(
            f"[CREATED] {ticket_channel} by {self.user} (ID: {self.channel_id})")
        return ticket_channel

#class Utility???
    # async def add(self, member: discord.Member):
    #     """adds a member to a ticket(try adding roles(typehint optional))

    #     Parameters
    #     ----------
    #     member : `discord.Member`
    #         member to be added\n
    #     """
    #     await self.channel.set_permissions(member, read_messages=True, send_messages=True)

    #     emby = await Others.make_embed(0x00FF00, f"{member.mention} was added")
    #     await self.channel.send(embed=emby)

    # async def remove(self, member: discord.Member):
    #     """remove a member to a ticket(try adding roles(typehint optional))

    #     Parameters
    #     ----------
    #     member : `discord.Member`
    #         member to be removed\n
    #     """
    #     await self.channel.set_permissions(member, read_messages=False, send_messages=False)
    #     emby = await Others.make_embed(0xff0000, f"{member.mention} was removed")
    #     await self.channel.send(embed=emby)

    # # async def survey(self):
    # #     member = get(self.client.get_all_members(), id=self.user_id)
    # #     print(member.name)
    # #     embed = discord.Embed(
    # #         title="Would you like to fill out a short survey? i̶f̶ ̶y̶o̶u̶ ̶d̶o̶n̶’̶t̶ ̶y̶o̶u̶ ̶w̶i̶l̶l̶ ̶b̶e̶ ̶b̶a̶n̶n̶e̶d̶")
    # #     message = await member.send(embed=embed)
    # #     form = ReactionForm(message, self.client, member)
    # #     form.set_timeout(60)
    # #     form.add_reaction("✅", True)
    # #     form.add_reaction("❌", False)
    # #     choice1 = await form.start()
    # #     print(f"Opt-in choice: {choice1}")
    # #     if choice1 is False:
    # #         return

    # #     embed = discord.Embed(title="Did your questions get answered?")
    # #     message = await member.send(embed=embed)
    # #     form = ReactionForm(message, self.client, member)
    # #     form.set_timeout(120)
    # #     form.add_reaction("✅", True)
    # #     form.add_reaction("❌", False)
    # #     choice2 = await form.start()
    # #     print(f"questions answered: {choice2}")

    # #     embed = discord.Embed(
    # #         title="How much did we help?(1 being the least - 5 being the most)")
    # #     message = await member.send(embed=embed)
    # #     form = ReactionForm(message, self.client, member)
    # #     form.set_timeout(120)
    # #     form.add_reaction("1️⃣", "one")
    # #     form.add_reaction("2️⃣", "two")
    # #     form.add_reaction("3️⃣", "three")
    # #     form.add_reaction("4️⃣", "four")
    # #     form.add_reaction("5️⃣", "five")
    # #     choice3 = await form.start()
    # #     print(choice3)

    # #     embed = discord.Embed(title="Anything else you would like to say?")
    # #     message = await member.send(embed=embed)
    # #     form = ReactionForm(message, self.client, member)
    # #     form.set_timeout(120)
    # #     form.add_reaction("✅", True)
    # #     form.add_reaction("❌", False)
    # #     choice4 = await form.start()
    # #     print(f"choice: {choice4}")
    # #     if choice4:
    # #         form = NaiveForm('Survey', member, self.client)
    # #         form.set_timeout(120)
    # #         # form.edit_and_delete(True) #wont work cuz dms
    # #         form.enable_cancelkeywords(False)
    # #         form.add_question('Anything else you would like to say?', 'second')
    # #         result = await form.start(member)
    # #         await member.send("Thank you for filling out this form!")

    # #         channel_log = get(
    # #             self.guild.text_channels, name="ticket-log")
    # #         print(type(channel_log))
    # #         await channel_log.send("test")
    # #         embed = discord.Embed(
    # #             title="Data", description=f"opt: {choice1}\nquestions answered: {choice2}\nrating: {choice3}, others: {result.second}")
    # #         await channel_log.send(embed=embed)

    # #         return result

class CloseTicket(BaseActions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, *kwargs)

    async def close_stats_helper(self, channel: discord.TextChannel) -> Tuple[List, int]:
        """will turn into a class later, rn just gets all the users in a channel

        Parameters
        ----------
        channel : `discord.TextChannel`
            channel to get users from\n

        Returns
        -------
        `List`: list of users from channel,
        `int`: number of messages
        """
        users = []
        count = 0
        async for msg in channel.history(limit=2000):
            if msg.author.name not in users:
                users.append(msg.author.name)
            count += 1

        channel_users = [self.guild.get_member_named(
            member) for member in users]
        return channel_users, count

    async def main(self):
        """closes a ticket"""
        current_status = db.get_status(self.channel_id)
        if current_status == "closed":
            await self.channel.send("Channel is already closed")
            return

        description = f"Ticket was closed by {self.user.mention}"
        embed = Embed(
            description=description,
            timestamp=datetime.datetime.utcnow(),
            color=0xFF0000)
        await self.channel.send(embed=embed)

        member = self.guild.get_member(self.user_id)
        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=None, send_messages=None),
            admin: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }
        category = await self._move_channel("Closed Tickets")

        await self.channel.edit(category=category)
        try:
            await self.channel.edit(overwrites=overwrites)
        except AttributeError:
            pass

        t_number, t_current_type, _, t_user = self._ticket_information()

        closed_name = Options.name_close(
            t_current_type, count=t_number, user=t_user)
        await self.channel.edit(name=closed_name)

        db._raw_update(
            "UPDATE requests SET channel_name = $1 WHERE channel_id = $2", (closed_name, self.channel_id,))
        stats_embed = discord.Embed(color=0xa0e9ec)

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

        transcript_message = await Others.transcript(self.channel, t_user, channel_log)
        if transcript_message is None:
            await self.channel.send("Transcript could not be sent to DMs")
        else:
            await self.channel.send("Transcript sent to DMs")
            stats_embed.add_field(name="transcript url",
                                  value=f"[transcript url]({config.TRANSCRIPT_DOMAIN}:{config.TRANSCRIPT_PORT}/direct?link={transcript_message.attachments[0].url} \"oreos taste good dont they\") ")

        channel_users, count = await self.close_stats_helper(self.channel)

        allmentions = '\n'.join([member.mention for member in channel_users])
        stats_embed.add_field(name="users", value=f"{allmentions}")
        stats_embed.add_field(name="number of messages", value=f"     {count}")
        await t_user.send(embed=stats_embed)

        status = "closed"
        db.update_status(status, self.channel_id,)

        admin_message = Embed(
            title="Closed Ticket Actions", description=""":unlock: Reopen Ticket\n:no_entry: Delete Ticket""",
            color=0xff0000)

        await self.channel.send(embed=admin_message, view=action_views.ReopenDeleteView())

        # await self.survey()

        await self._log_to_channel("Closed ticket")
        log.info(
            f"[CLOSED] {self.channel} by {self.user} (ID: {self.channel_id})")

class ReopenTicket(BaseActions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def reopen(self):
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
        embed = Embed(
            description=f"Ticket was re-opened by {self.user.mention}",
            timestamp=datetime.datetime.utcnow(),
            color=0xFF0000)
        msg = await self.channel.send(embed=embed, view=action_views.DeleteView())

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
        try:
            db_channel_name = db.get_channel_name(self.channel_id)
            if db_channel_name is None:
                raise TypeError("channel does not exist in db")
        except Exception as e:
            if isinstance(e, TypeError):
                await self.channel.send("Channel is not a ticket")
            else:
                log.exception(e)
                await self.channel.send("Channel isn't a ticket")
            return

        embed = Embed(
            title="Deleting ticket",
            description="5 seconds left",
            color=0xf7fcfd)
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
