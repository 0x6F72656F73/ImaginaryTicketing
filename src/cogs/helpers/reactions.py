from typing import List
import datetime
import asyncio
import logging

import discord
from discord import Embed
from discord.utils import get
from discord.ext import commands
# from discord.ext.forms import NaiveForm, ReactionForm

import config
from utils.others import Others
from utils.options import Options
from utils.database.db import DatabaseManager as db

log = logging.getLogger(__name__)

class Reactions(commands.Cog):
    """handles all reactions"""

    def __init__(self, bot: commands.Bot, client, guild_id: int, guild: str, user_id: int, user: str,
                 channel_id: int, channel: str, message_id: int,
                 cmd: bool, payload: discord.RawReactionActionEvent, emoji: str = None, emoji_raw: discord.partial_emoji.PartialEmoji = None, background: bool = False):
        self.bot = bot
        self.client = client
        self.guild_id = guild_id
        self.guild = guild
        self.user_id = user_id
        self.user = user
        self.channel_id = channel_id
        self.channel = channel
        self.message_id = message_id
        self.emoji = emoji
        self.payload = payload
        self.cmd = cmd
        self.background = background
        self.emoji_raw = emoji_raw

    async def log_to_channel(self, msg: str, is_bot=False):
        """Logs a message to channel ticket-log

        Parameters
        ----------
        msg : `str`
            message to log\n
        is_bot : `bool`, optional
            if its a bot, use bot name/pfp, by default False
        """
        if self.background:
            is_bot = True
        channel_log = get(
            self.guild.text_channels, name="ticket-log")
        if is_bot:
            logembed = await Others.log_embed(
                msg, self.user.user, self.user.user.avatar_url, self.channel)
        else:
            logembed = await Others.log_embed(
                msg, self.user, self.user.avatar_url, self.channel)
        await channel_log.send(embed=logembed)

    async def create(self):
        """Creates a ticket"""
        ticket_id_list = db.get_all_ticket_channel_messages(self.guild_id)
        if not self.message_id in ticket_id_list and self.cmd is not True:
            return
        if self.emoji is not None and self.cmd is not True:
            # if reaction
            message = await self.channel.fetch_message(self.message_id)
            if self.emoji_raw is None:
                await message.remove_reaction(self.emoji, self.user)
            else:
                await message.remove_reaction(self.emoji_raw, self.user)
            emoji_type = Others.emoji_to_string(self.emoji)
        else:
            # if command
            try:
                dict_values = {'help': 'help',
                               'submit': 'submit', 'misc': 'misc'}
                emoji_type = dict_values[self.emoji]
            except KeyError:
                await self.channel.send("possible ticket types are help, submit, and misc")
                return
        # get information
        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        member = self.guild.get_member(self.user_id)
        if admin not in member.roles:
            # Limit tickets for non admin members
            n_tickets = db._raw_select(
                "SELECT count(1) FROM (SELECT * FROM requests WHERE ticket_type=$1 and user_id=$2)", (emoji_type, self.user_id,), fetch_one=True)
            current = n_tickets[0]
            limit = Options.limit(emoji_type)
            if current >= limit:
                emby = await Others.make_embed(
                    0x00FFFF, f"You have reached the maximum limit ({current}/{limit}) for this ticket type")
                await self.user.send(embed=emby)
                return

        # get information
        number = db.get_number_new(emoji_type)
        cat = Options.full_category_name(emoji_type)
        category = get(self.guild.categories, name=cat)
        good_channel_name = Options.name_open(emoji_type, number, self.user)
        if category is None:
            new_category = await self.guild.create_category(name=cat)
            category = self.guild.get_channel(new_category.id)

        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            admin: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }

        # create new text channel
        ticket_channel_name = await category.create_text_channel(good_channel_name, overwrites=overwrites)
        ticket_channel_id = ticket_channel_name.id

        # update status in db
        status = "open"
        checked = "0"
        db._raw_insert("INSERT INTO requests (channel_id, channel_name, guild_id, user_id, user_name, ticket_type, status, checked) VALUES ($1,$2,$3,$4,$5,$6,$7,$8 )", (
            ticket_channel_id, str(ticket_channel_name), self.guild.id, self.user_id, str(self.user), emoji_type, status, checked))

        avail_mods = get(
            self.guild.roles, name=config.TICKET_PING_ROLE)
        # send messages
        if not emoji_type == "submit":
            welcome_message = f'Welcome <@{self.user_id}>,\nA new ticket has been opened {avail_mods.mention}\n\n'
        else:
            welcome_message = f'Welcome <@{self.user_id}>\n\n'
        message = Options.message(emoji_type, avail_mods)

        embed = await Others.make_embed(0x5dc169, message)
        ticket_channel_message = await ticket_channel_name.send(welcome_message, embed=embed)

        await ticket_channel_message.pin()

        ticket_channel = get(
            self.guild.text_channels, id=ticket_channel_id)
        await ticket_channel.purge(limit=1)
        await ticket_channel_message.add_reaction("🔒")

        await self.log_to_channel("Created ticket")
        log.info(
            f"[CREATED] {ticket_channel_name} by {self.user} (ID: {self.channel_id})")

    async def add(self, member: discord.Member):
        """adds a member to a ticket(try adding roles(typehint optional))

        Parameters
        ----------
        member : `discord.Member`
            member to be added\n
        """
        await self.channel.set_permissions(member, read_messages=True, send_messages=True)

        emby = await Others.make_embed(0x00FF00, f"{member.mention} was added")
        await self.channel.send(embed=emby)

    async def remove(self, member: discord.Member):
        """remove a member to a ticket(try adding roles(typehint optional))

        Parameters
        ----------
        member : `discord.Member`
            member to be removed\n
        """
        await self.channel.set_permissions(member, read_messages=False, send_messages=False)
        emby = await Others.make_embed(0xff0000, f"{member.mention} was removed")
        await self.channel.send(embed=emby)

    async def close_stats_helper(self, channel: discord.TextChannel) -> [List, int]:
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
        messages = 0
        async for msg in channel.history(limit=2000):
            if msg.author.name not in users:
                users.append(msg.author.name)
            messages += 1
        return users, messages

    # async def survey(self):
    #     member = get(self.client.get_all_members(), id=self.user_id)
    #     print(member.name)
    #     embed = discord.Embed(
    #         title="Would you like to fill out a short survey? i̶f̶ ̶y̶o̶u̶ ̶d̶o̶n̶’̶t̶ ̶y̶o̶u̶ ̶w̶i̶l̶l̶ ̶b̶e̶ ̶b̶a̶n̶n̶e̶d̶")
    #     message = await member.send(embed=embed)
    #     form = ReactionForm(message, self.client, member)
    #     form.set_timeout(60)
    #     form.add_reaction("✅", True)
    #     form.add_reaction("❌", False)
    #     choice1 = await form.start()
    #     print(f"Opt-in choice: {choice1}")
    #     if choice1 is False:
    #         return

    #     embed = discord.Embed(title="Did your questions get answered?")
    #     message = await member.send(embed=embed)
    #     form = ReactionForm(message, self.client, member)
    #     form.set_timeout(120)
    #     form.add_reaction("✅", True)
    #     form.add_reaction("❌", False)
    #     choice2 = await form.start()
    #     print(f"questions answered: {choice2}")

    #     embed = discord.Embed(
    #         title="How much did we help?(1 being the least - 5 being the most)")
    #     message = await member.send(embed=embed)
    #     form = ReactionForm(message, self.client, member)
    #     form.set_timeout(120)
    #     form.add_reaction("1️⃣", "one")
    #     form.add_reaction("2️⃣", "two")
    #     form.add_reaction("3️⃣", "three")
    #     form.add_reaction("4️⃣", "four")
    #     form.add_reaction("5️⃣", "five")
    #     choice3 = await form.start()
    #     print(choice3)

    #     embed = discord.Embed(title="Anything else you would like to say?")
    #     message = await member.send(embed=embed)
    #     form = ReactionForm(message, self.client, member)
    #     form.set_timeout(120)
    #     form.add_reaction("✅", True)
    #     form.add_reaction("❌", False)
    #     choice4 = await form.start()
    #     print(f"choice: {choice4}")
    #     if choice4:
    #         form = NaiveForm('Survey', member, self.client)
    #         form.set_timeout(120)
    #         # form.edit_and_delete(True) #wont work cuz dms
    #         form.enable_cancelkeywords(False)
    #         form.add_question('Anything else you would like to say?', 'second')
    #         result = await form.start(member)
    #         await member.send("Thank you for filling out this form!")

    #         channel_log = get(
    #             self.guild.text_channels, name="ticket-log")
    #         print(type(channel_log))
    #         await channel_log.send("test")
    #         embed = discord.Embed(
    #             title="Data", description=f"opt: {choice1}\nquestions answered: {choice2}\nrating: {choice3}, others: {result.second}")
    #         await channel_log.send(embed=embed)

    #         return result

    async def close(self):
        """closes a ticket"""
        if self.emoji is not None:
            #if reaction
            message = await self.channel.fetch_message(self.message_id)
            await message.remove_reaction(self.emoji, self.user)

        #if closed do nothing
        try:
            current_status = db.get_status(self.channel_id)
        except:
            return
        if current_status == "closed":
            await self.channel.send("Channel is already closed")
            return

        #send closed message
        if self.background:
            description = f"Ticket was closed by {self.user.user.mention}"
        else:
            description = f"Ticket was closed by {self.user.mention}"
        embed = Embed(
            description=description,
            timestamp=datetime.datetime.utcnow(),
            color=0xFF0000)

        await self.channel.send(embed=embed)

        #get information
        db_channel_name = db.get_channel_name(self.channel_id)
        discord_db_channel = get(
            self.guild.text_channels, name=db_channel_name)
        member = self.guild.get_member(self.user_id)
        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=None, send_messages=None),
            admin: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }
        try:
            await discord_db_channel.edit(overwrites=overwrites)
        except AttributeError:
            pass

        #get information
        number = db.get_number_previous(self.channel.id)
        current_type = db.get_ticket_type(self.channel_id)
        user_id = db.get_user_id(self.channel_id)
        user = self.guild.get_member(user_id)
        #change channel name
        closedname = Options.name_close(current_type, count=number, user=user)
        await self.channel.edit(name=closedname)

        db._raw_update(
            "UPDATE requests SET channel_name = $1 WHERE channel_id = $2", (closedname, self.channel_id,))
        coolembed = discord.Embed(color=0xa0e9ec)
        #send transcript
        try:
            transcript_message = await Others.transcript(self.channel, user)
            channel_log_category = get(
                self.guild.categories, name=config.LOG_CHANNEL_CATEGORY)
            if channel_log_category is None:
                await self.channel.send("logs category does not exist")
                return

            channel_log = get(
                self.guild.text_channels, category=channel_log_category, name="ticket-log")
            if channel_log is None:
                await self.channel.send("ticket-log channel does not exist in category log")
                return

            await Others.transcript(self.channel, channel_log)
            await self.channel.send("Transcript sent to DMs")
            coolembed.add_field(name="transcript url",
                                value=f"[transcript url](https://oreos.imaginaryctf.org:1337/direct?link={transcript_message.attachments[0].url} \"oreos taste good dont they\") ")
        except Exception as e:
            log.exception(str(e))
            await self.channel.send("Transcript could not be sent to DMs")
        users, count = await self.close_stats_helper(self.channel)
        discord_users = []
        for member in users:
            member_true = self.guild.get_member_named(member)
            if member_true is None:
                continue
            log.info(member)
            discord_users.append(member_true)

        allmentions = '\n'.join([member.mention for member in discord_users])
        coolembed.add_field(name="users", value=f"{allmentions}")
        coolembed.add_field(name="number of messages", value=f"     {count}")
        await user.send(embed=coolembed)
        #update/set closed messages
        status = "closed"
        db.update_status(status, self.channel_id,)

        admin_message = Embed(
            title="Closed Ticket Actions", description="""
:unlock: Reopen Ticket
:no_entry: Delete Ticket
            """, color=0xff0000)
        ticket_admin_message = await self.channel.send(embed=admin_message)
        await ticket_admin_message.add_reaction("🔓")
        # thats an unlocked lock
        await ticket_admin_message.add_reaction("⛔")

        # await self.survey()

        await self.log_to_channel("Closed ticket")
        if self.background:
            log.info(
                f"[CLOSED] {self.channel} by {self.user.user} (ID: {self.channel_id})")

        else:
            log.info(
                f"[CLOSED] {self.channel} by {self.user} (ID: {self.channel_id})")

    async def reopen_ticket(self):
        """reopens a ticket"""
        if self.emoji is not None:
            # if reaction
            message = await self.channel.fetch_message(self.message_id)
            await message.remove_reaction(self.emoji, self.user)

        #if open do nothing
        try:
            test_status = db.get_status(self.channel_id)
            if test_status == "open":
                await self.channel.send("Channel is already open")
                return
        except:
            return

        #send reopened message
        status = "open"
        db.update_status(status, self.channel_id)
        embed = Embed(
            description=f"Ticket was re-opened by {self.user.mention}",
            timestamp=datetime.datetime.utcnow(),
            color=0xFF0000)
        msg = await self.channel.send(embed=embed)
        await msg.add_reaction("🔒")

        #get information
        number = db.get_number_previous(self.channel_id)
        current_type = db.get_ticket_type(self.channel_id)

        user_id = db.get_user_id(self.channel_id)
        current_name = self.client.get_user(user_id)

        reopened = Options.name_open(
            current_type, count=number, user=current_name)
        await self.channel.edit(name=reopened)
        db._raw_update(
            "UPDATE requests set channel_name = $1 WHERE channel_id = $2", (reopened, self.channel_id,))

        db_channel_name = db.get_channel_name(self.channel_id)
        discord_db_channel = get(
            self.guild.text_channels, name=db_channel_name)
        member = self.guild.get_member(user_id)
        admin = get(self.guild.roles, name=config.ADMIN_ROLE)
        overwrites = {
            self.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            admin: discord.PermissionOverwrite(
                read_messages=True, send_messages=True)
        }
        await discord_db_channel.edit(overwrites=overwrites)

        await self.log_to_channel("Re-Opened ticket")
        log.info(
            f"[RE-OPENED] {self.channel} by {self.user} (ID: {self.channel_id})")

    async def delete(self):
        """deletes a ticket"""

        if self.emoji is not None:
            #if reaction
            message = await self.channel.fetch_message(self.message_id)
            await message.remove_reaction(self.emoji, self.user)
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

        #send deleted message
        embed = Embed(
            title="Deleting ticket",
            description="5 seconds left",
            color=0xf7fcfd)
        await self.channel.send(embed=embed)
        await asyncio.sleep(5)
        await self.channel.delete()

        #update information in db
        db._raw_insert(
            "INSERT INTO archive SELECT * FROM requests WHERE channel_id= $1", (self.channel_id,))

        db._raw_delete(
            "DELETE FROM requests WHERE channel_id = $1", (self.channel_id,))

        await self.log_to_channel("Deleted ticket")
        log.info(
            f"[DELETED] {self.channel} by {self.user} (ID: {self.channel_id})")
