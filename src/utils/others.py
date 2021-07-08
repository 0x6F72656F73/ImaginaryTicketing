import io
import asyncio
import random
from typing import Any, NamedTuple
from datetime import datetime
import logging

import discord
from discord.ext import commands
from discord import Webhook, AsyncWebhookAdapter
import aiohttp
import chat_exporter

import config

log = logging.getLogger(__name__)

class Others(commands.Cog):
    """Abstract helper methods"""

    @staticmethod
    async def transcript(channel, user: discord.Member = None, to_channel: discord.TextChannel = None):
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
        transcript = await chat_exporter.export(channel, None, "America/Los_Angeles")

        if transcript is None:
            return

        transcript_file = discord.File(io.BytesIO(transcript.encode()),
                                       filename=f"transcript-{channel}.html")
        if to_channel is None:
            message = await user.send(file=transcript_file)
        elif user is None:
            message = await to_channel.send(file=transcript_file)
        else:
            await log.critical("log could not be sent anywhere")
        with open(f"transcripts/transcript-{channel}.html", "w+") as file:
            file.write(transcript)

        return message

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
        embed = discord.Embed(title=f"{title}",
                              timestamp=datetime.utcnow(), color=0xff0000)
        embed.set_author(name=f"{user}", icon_url=f"{avatar_url}")
        embed.add_field(name="Channel",
                        value=f"{channel_name}")
        return embed

    @staticmethod
    def emoji_to_string(emoji: str) -> str:
        """converters an emoji to string for db actions

        Parameters
        ----------
        emoji : `str`
            emoji to be converted\n

        Returns
        -------
        `str`: string representation of the emoji
        """
        emoji_list = config.EMOJIS
        dict_values = {emoji_list[0]: 'help',
                       emoji_list[1]: 'submit',
                       emoji_list[2]: 'misc'}
        return dict_values[emoji]

    @staticmethod
    async def make_embed(color: str, desc: Any) -> discord.embeds.Embed:
        """returns an embed with no fields

        Parameters
        ----------
        color : `str`
            the color of the embed\n
        desc : `Any`
            the description of the embed\n

        Returns
        -------
        `discord.embeds.Embed`: the returned embed
        """
        embed = discord.Embed(description=desc,
                              timestamp=datetime.utcnow(), color=color)
        return embed

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
    async def say_in_webhook(member, channel, avatar_url, allow_mention, args, return_message=False):
        avatar = await member.avatar_url.read()
        webhooks = await channel.webhooks()

        if len(webhooks) == 0:
            send_web_hook = await channel.create_webhook(
                name="Tickets", avatar=avatar)
        else:
            webhook_times = [webhook.created_at for webhook in webhooks]

            shortest = min(webhook_times)
            for webhook in webhooks:
                if webhook.created_at == shortest:
                    send_web_hook = webhook
                    break

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(
                send_web_hook.url, adapter=AsyncWebhookAdapter(session))
            if allow_mention is True:
                message = await webhook.send(f'{args}', username=f'{member.display_name}', avatar_url=avatar_url, wait=True)

            else:
                message = await webhook.send(f'{args}', username=f'{member.display_name}', avatar_url=avatar_url, allowed_mentions=discord.AllowedMentions.none())
        if return_message:
            return channel.get_partial_message(message.id)

    @staticmethod
    async def random_member_webhook(guild):
        role = discord.utils.get(guild.roles, name=config.ADMIN_ROLE)
        person = random.choice(role.members)
        return person

    @staticmethod
    class Challenge(NamedTuple):
        id_: int
        author: str
        title: str
        ignore: bool = False

        def __repr__(self):
            return self.title
