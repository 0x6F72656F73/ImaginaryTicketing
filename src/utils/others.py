import io
import asyncio
import random
from typing import Any, NamedTuple
import logging

import discord
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
                              timestamp=discord.utils.utcnow(), color=0xff0000)
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
    async def make_embed(color: str, desc: Any, **kwargs) -> discord.embeds.Embed:
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
                              timestamp=discord.utils.utcnow(), color=color, **kwargs)
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
