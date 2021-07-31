import io
import asyncio
import random
from typing import Any, NamedTuple
import logging

import discord
from discord import Embed
from discord.ext import commands
import chat_exporter

import config

log = logging.getLogger(__name__)

class Others(commands.Cog):
    """Abstract helper methods"""

    @staticmethod
    async def transcript(channel, user: discord.User = None, to_channel: discord.TextChannel = None) -> discord.Message:
        """send a transcript of a channel to a user or a channel

        Parameters
        ----------
        channel : `type`
            channel to get transcirpt of\n
        user : `discord.Member`, `optional`
            user to send transcript to, by default None\n
        to_channel : `discord.TextChannel`, `optional`\n
            channel to send transcript to, by default None
        """
        if not user and not to_channel:
            await channel.send("log could not be sent anywhere")
            return

        transcript = await chat_exporter.export(channel, None, "America/Los_Angeles")
        if transcript is None:
            return

        if to_channel:
            transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                           filename=f"transcript-{channel}.html")
            message = await to_channel.send(file=transcript_file)

        if user:
            transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                           filename=f"transcript-{channel}.html")
            message = await user.send(file=transcript_file)

        with open(f"transcripts/transcript-{channel}.html", "w+") as file:
            file.write(transcript)

        return message, discord.File(io.BytesIO(transcript.encode()),
                                     filename=f"transcript-{channel}.html")

    @staticmethod
    async def log_embed(title: str, user: discord.user.User, avatar_url: discord.asset.Asset, channel_name: discord.channel.TextChannel) -> discord.Embed:
        """makes an embed to be logged

        Parameters
        ----------
        title : `str`
            title of the embed\n
        user : `discord.user.User`
            user to send embed to\n
        avatar_url : `discord.asset.Asset`
            url of the user\n
        channel_name : `discord.channel.TextChannel`
            channel to send embed to\n

        Returns
        -------
        `discord.embeds.Embed`: an embed
        """
        embed = Others.Embed(title=f"{title}",
                             timestamp=discord.utils.utcnow())
        embed.set_author(name=f"{user}", icon_url=f"{avatar_url}")
        embed.add_field(name="Channel",
                        value=f"{channel_name}")
        return embed

    @staticmethod
    class Embed(Embed):
        """returns an embed with a random color

        Returns
        -------
        `discord.embeds.Embed`: the embed
        """

        def __new__(cls, **kwargs) -> discord.embeds.Embed:
            return discord.Embed(color=discord.Color.random(), **kwargs)

    @staticmethod
    async def delmsg(ctx, time: int = 1):
        """deletes a message after (time)

        Parameters
        ----------
        ctx : `discord.ext.commands.context.Context`
            discord context\n
        time : `int`, `optional`
            time to wait until deleting the message, by default 1
        """
        await asyncio.sleep(time)
        await ctx.message.delete()

    @staticmethod
    async def say_in_webhook(bot: discord.ext.commands.Bot, member: discord.Member, channel: discord.TextChannel, avatar_url: discord.Asset.url, allow_mention: bool, message, return_message: bool = False, **kwargs):
        avatar = await member.avatar.read()
        webhooks = await channel.webhooks()

        if len(webhooks) == 0:
            send_web_hook = await channel.create_webhook(
                name="Tickets", avatar=avatar)
        else:
            webhook_times = [webhook.created_at for webhook in webhooks]

            shortest = min(webhook_times)
            for hook in webhooks:
                if hook.created_at == shortest:
                    send_web_hook = hook
                    break

        webhook = await bot.fetch_webhook(send_web_hook.id)
        if allow_mention is True:
            ret_message = await webhook.send(f'{message}', username=f'{member.display_name}', avatar_url=avatar_url, wait=True, **kwargs)
        else:
            ret_message = await webhook.send(f'{message}', username=f'{member.display_name}', avatar_url=avatar_url, allowed_mentions=discord.AllowedMentions.none(), **kwargs)
        if return_message:
            return channel.get_partial_message(ret_message.id)

    @staticmethod
    async def random_admin_member(guild) -> discord.Member:
        role = discord.utils.get(guild.roles, name=config.ADMIN_ROLE)
        person = random.choice(role.members)
        return person

    @staticmethod
    class Challenge(NamedTuple):
        id_: int
        title: str
        author: str
        category: str
        ignore: bool = False

        def __repr__(self):
            return f"{self.title}({self.id_}, {self.author}, {self.category}, {self.ignore})"
