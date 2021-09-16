import io
import random
from datetime import datetime
from typing import NamedTuple, Tuple, Union
import logging

import discord
from discord.ext import commands
import chat_exporter

import config

log = logging.getLogger(__name__)

class UI:
    @classmethod
    def log_embed(cls, title: str, channel: discord.TextChannel, user: discord.user.User = None, avatar_url: discord.asset.Asset = None, **kwargs) -> discord.Embed:
        """makes an embed to be logged

        Parameters
        ----------
        title : `str`
            title of the embed\n
        user : `discord.user.User`
            user to send embed to\n
        avatar_url : `discord.asset.Asset`
            url of the user\n
        channel_name : `discord.TextChannel`
            channel to send embed to\n

        Returns
        -------
        `discord.embeds.Embed`: an embed
        """
        embed = cls.Embed(title=f"{title}", **kwargs)
        if user is not None:
            embed.set_author(name=f"{user}", icon_url=f"{avatar_url}")
        embed.add_field(name="Channel",
                        value=f"{channel.name}- {channel.id}")
        return embed

    @classmethod
    async def log_to_logs(cls, title: str, channel_name: discord.TextChannel, user: discord.user.User = None, **kwargs):
        """Logs a message to ticket logs

        Parameters
        ----------
        msg : `str`
            message to log
        user : `discord.user.User`
            user that did the action
        channel_name : `discord.TextChannel`
            channel the action occurred in
        """
        if user is not None:
            log_embed = cls.log_embed(
                title, channel_name, user, user.avatar.url, **kwargs)
        else:
            log_embed = cls.log_embed(
                title, channel_name, **kwargs)
        log_channel = discord.utils.get(
            channel_name.guild.text_channels, name=config.logs['name'])
        await log_channel.send(embed=log_embed)

    @staticmethod
    class Embed(discord.Embed):
        """returns an embed with a random color

        Returns
        -------
        `discord.embeds.Embed`: the embed
        """

        def __new__(cls, **kwargs) -> discord.Embed:
            kwargs.setdefault('timestamp', discord.utils.utcnow())
            return discord.Embed(color=discord.Color.random(), **kwargs)

    @staticmethod
    def add_to_description(embed: discord.Embed, text):
        if len(embed.description) == 0:
            embed.description = f"{text}\n"
        else:
            embed.description += f"{text}\n"

class Utility:
    """Abstract helper methods"""

    @staticmethod
    async def transcript(channel: discord.TextChannel, destination: Union[discord.User, discord.TextChannel]) -> Tuple[discord.Message, discord.File]:
        """send a transcript of a channel to a user or a channel

        Parameters
        ----------
        channel : `discord.TextChannel`
            channel to get transcirpt of\n
        destination : `Union[discord.User, discord.TextChannel]`
            place to send transcript to\n

        Returns
        -------
        `Tuple[discord.Message, discord.File]`: The message with the transcript sent as reference to the transcript
        """
        transcript = await chat_exporter.export(channel, None, "America/Los_Angeles")
        if transcript is None:
            return

        filename = f"transcript-{channel}-{channel.id}.html"
        transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                       filename=filename)
        message = await destination.send(file=transcript_file)

        with open('transcripts/' + '-'.join(filename.split('-')[1:]), "w+") as file:
            file.write(transcript)

        return message, discord.File(io.BytesIO(transcript.encode()),
                                     filename=filename)

    @staticmethod
    async def delete_message(ctx, time: int = 1):
        """deletes a message after (time)

        Parameters
        ----------
        ctx : `discord.ext.commands.Context`
            discord context\n
        time : `int`, `optional`
            time to wait until deleting the message, by default 1
        """
        await ctx.message.delete(delay=time)

    @staticmethod
    async def say_in_webhook(bot: commands.Bot, member: discord.Member, channel: discord.TextChannel, avatar_url: discord.Asset.url, allow_mention: bool, message: str, return_message: bool = False, **kwargs):
        avatar = await member.avatar.read()
        webhooks = await channel.webhooks()

        if len(webhooks) == 0 or len([hook for hook in webhooks if hook.name == "Tickets"]) == 0:
            send_web_hook = await channel.create_webhook(
                name="Tickets", avatar=avatar)
        else:
            webhook_times = [
                hook.created_at for hook in webhooks if hook.name == "Tickets"]

            shortest = min(webhook_times)
            for hook in webhooks:
                if hook.created_at == shortest:
                    send_web_hook = hook
                    break

        webhook = await bot.fetch_webhook(send_web_hook.id)
        if allow_mention is True:
            ret_message = await webhook.send(f'{message}', username=f'{member.display_name}', avatar_url=avatar_url, wait=True, **kwargs)
        else:
            ret_message = await webhook.send(f'{message}', username=f'{member.display_name}', avatar_url=avatar_url, wait=True, allowed_mentions=discord.AllowedMentions.none(), **kwargs)
        if return_message:
            return channel.get_partial_message(ret_message.id)

    @staticmethod
    async def random_admin_member(guild) -> discord.Member:
        role = discord.utils.get(guild.roles, name=config.roles['admin'])
        person = random.choice(role.members)
        return person

class Challenge(NamedTuple):
    id: int
    title: str
    author: str
    category: str
    ignore: bool = False
    helper_id_list: str = str([])

    def __repr__(self):
        return f"{self.title}({self.id}, {self.author}, {self.category}, {self.ignore})"

class TrelloChallenge(NamedTuple):  # put in utility
    id: int
    title: str
    author: str
    category: str
    points: int
    release_date: datetime

    def __repr__(self):
        return f"{self.title}({self.id}, {self.author}, {self.category}, {self.points}, {self.release_date})"

    @classmethod
    def build(cls, **kwargs):
        kwargs = {k: v for (k, v) in kwargs.items() if k in cls._fields}
        return cls(**kwargs)
