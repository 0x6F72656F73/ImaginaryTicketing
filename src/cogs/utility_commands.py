import asyncio
from collections import defaultdict
import json
import typing
import logging

import discord
from discord.ext import commands
from discord.utils import get

import config

from utils.database.db import DatabaseManager as db
from utils.background import ScrapeChallenges, UpdateHelpers
from utils.utility import Utility, UI, Challenge
from utils import exceptions, types

log = logging.getLogger(__name__)

class UtilityCommands(commands.Cog):
    """Misc utility commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="say")
    async def say(self, ctx, *, message):
        """says a message through a webhook"""

        await Utility.say_in_webhook(self.bot, ctx.author, ctx.channel, ctx.author.avatar.url, False, message)
        await ctx.message.delete()

    @commands.command(name="sayuser", aliases=["sayu"])
    @commands.has_role(config.roles['admin'])
    async def saymember(self, ctx, user: discord.User, *, message):
        """says a message through a webhook through the specified user"""
        await Utility.say_in_webhook(self.bot, user, ctx.channel, user.avatar.url, False, message)
        await ctx.message.delete()

    @commands.command(name="about")
    async def about(self, ctx):
        """returns about info"""
        embed = UI.Embed(title="about",
                         description="This bot was proudly made by 0x6F72656F73#8221 :cookie:")
        await ctx.send(embed=embed)

    @commands.command(name="purge")
    @commands.has_role(config.roles['admin'])
    async def purge(self, ctx, limit: int):
        """purges x amount of messages"""
        await ctx.channel.purge(limit=limit + 1)
        await ctx.send(f'Purged {limit} messages', delete_after=3)

    @commands.command(name="check")
    @commands.has_role(config.roles['admin'])
    async def check_discord(self, ctx):
        """Checks if all configurations are valid"""
        bot_in_guild = ctx.guild.get_member(self.bot.user.id)
        checks = {'pass': [], 'fail': []}
        all_checks = {**{f"{k} role": bool(get(ctx.guild.roles, name=v)) for (k, v) in config.roles.items()},
                      "channel log category": bool(get(ctx.guild.categories, name=config.logs["category"])),
                      "channel log name": bool(get(ctx.guild.text_channels, name=config.logs["name"])),
                      "is admin": bool(bot_in_guild.guild_permissions.administrator)}
        checks['pass'] = [check for check,
                          status in all_checks.items() if status is True]
        checks['fail'] = [check for check,
                          status in all_checks.items() if status is False]

        embed = UI.Embed(title="Checks")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")

        UI.add_to_description(embed, "**Successful checks:**")
        for check in checks['pass']:
            UI.add_to_description(embed, f"- {check}")

        UI.add_to_description(embed, "**Failed checks:**")
        for check in checks['fail']:
            UI.add_to_description(embed, f"- {check}")

        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @commands.command(name="config")
    @commands.has_role(config.roles['admin'])
    async def get_config_value(self, ctx, target_field: str = None):
        """Shows the configuration for all fields or a given field"""
        def find_value(field):
            return json.dumps(getattr(config, field), sort_keys=True, indent=4)

        if target_field is None:
            embed = UI.Embed(title="config")
            embed.set_author(name=f"{ctx.author}",
                             icon_url=f"{ctx.author.avatar.url}")

            configrations = [f"{c}: {find_value(c)}"
                             for c in config.__dict__ if not c.startswith("__")]
            seperator = ',\n'
            embed.description = f"```json\n{seperator.join(configrations)}```"

            await ctx.message.delete()
            return await ctx.channel.send(embed=embed)
        try:
            configration = f"{target_field}: {find_value(target_field.lower())}"
            embed = UI.Embed(title=f"config- {target_field}")
            embed.set_author(name=f"{ctx.author}",
                             icon_url=f"{ctx.author.avatar.url}")

            embed.description = f"```json\n{configration}```"
            await ctx.channel.send(embed=embed)
        except AttributeError:
            fields = '\n'.join({field for field in dir(config)
                                if not field.startswith("__")})
            embed = UI.Embed(
                title="invalid field", description=f'Possible fields are:\n{fields}')
            embed.set_author(name=f"{ctx.author}",
                             icon_url=f"{ctx.author.avatar.url}")

            await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @commands.group(name="challenge", aliases=["c", "chall"], invoke_without_command=True)
    @commands.has_role(config.roles['admin'])
    async def challenge(self, ctx):
        """Base challenge command. Shows stats on challenges."""
        embed = UI.Embed(title="Challenges")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")

        challenges = [Challenge(*list(challenge))
                      for challenge in db.get_all_challenges()]
        challenges_by_category = defaultdict(list)
        for challenge in challenges:
            challenges_by_category[challenge.category].append(challenge)
        for category, challenge_list in challenges_by_category.items():
            embed.add_field(name=category, value='=' *
                            int(len(category) * .9), inline=False)
            for challenge in challenge_list:
                embed.add_field(
                    name=challenge.title, value='_ _', inline=True)
        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @challenge.command(name="refresh", aliases=["ref"])
    @commands.has_role(config.roles['admin'])
    async def refresh(self, ctx):
        """refreshes challenges from the api"""
        embed = UI.Embed(
            description="sending requests...")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")

        await ctx.message.delete()
        message = await ctx.channel.send(embed=embed)

        await ScrapeChallenges.main(self.bot)

        embed.description = "challenges refreshed"
        await message.edit(embed=embed)

    @commands.group(name="helper", aliases=["h"], invoke_without_command=True)
    @commands.has_role(config.roles['helper'])
    async def helper_user(self, ctx):
        """Base helper-user command. Shows helper's stats"""
        try:
            status = db.get_helper_status(ctx.author.id)
        except ValueError as e:
            return await ctx.channel.send(e.args[0])

        embed = UI.Embed(
            title=f"{ctx.author.name}", description=f'status: {status}')
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")

        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @helper_user.command(name="status", aliases=["s"])
    @commands.has_role(config.roles['helper'])
    async def helper_user_change_status(self, ctx, status: int):
        """changes your availability status: 1 or 0"""
        if not status in typing.get_args(types.HelperAvailable):
            return await ctx.channel.send("choice must be 1 or 0")

        db.update_helper_status(ctx.author.id, status)

        if status == 1:
            await ctx.channel.send("you will now be added to any future tickets for challenges you have solved")
        else:
            await ctx.channel.send("you will now not be added to any future tickets for challenges you have solved")

    @helper_user.command(name="sync", aliases=["sy"])
    @commands.has_role(config.roles['helper'])
    async def helper_user_sync(self, ctx, choice: str):
        """updates you to channels: add or remove"""
        choice_ = choice
        try:
            choice = getattr(types.HelperSync, choice.upper())
        except AttributeError:
            return await ctx.channel.send("choice must be either add or remove")
        try:
            await UpdateHelpers.modify_helpers_to_channel(self.bot, member_id=ctx.author.id, choice=choice.value)
        except exceptions.HelperSyncError as e:
            return await ctx.channel.send(e.args[0])

        choice_ = f"{choice_}ed to" if choice_[-1:
                                               ] != 'e' else f"{choice_[:-1]}ed from"
        embed = UI.Embed(
            description=f"{choice_} all tickets")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")
        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @helper_user.group(name="admin", aliases=["a"], invoke_without_command=True)
    @commands.has_role(config.roles['admin'])
    async def helper_admin(self, ctx):
        """Base helper-admin command. Shows stats on helpers."""
        helper_role = get(ctx.guild.roles, name=config.roles['helper'])
        if len(helper_role.members):
            helper_ids = [helper.id for helper in helper_role.members]
            db_helpers = db.get_all_helpers()
            helpers = set(helper_ids).intersection(db_helpers)

            helpers = '\n'.join(
                [member.mention for member in helper_role.members if member.id in helpers])
        else:
            helpers = 'No helpers'

        embed = UI.Embed(
            title=f"{config.roles['helper']}", description=helpers)
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")

        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @helper_admin.command(name="add")
    @commands.has_role(config.roles['admin'])
    async def helper_add(self, ctx, member: discord.Member):
        """adds a helper"""
        helper_role = get(member.guild.roles, name=config.roles['helper'])
        helper_ids = [helper.id for helper in helper_role.members]
        if member.id in helper_ids:
            embed = UI.Embed(
                description=f"Member {member.mention} already has role {config.roles['helper']}")
            embed.set_author(name=f"{ctx.author}",
                             icon_url=f"{ctx.author.avatar.url}")

            await ctx.message.delete()
            return await ctx.channel.send(embed=embed)

        await member.add_roles(helper_role)
        db.create_helper(member.id)

        embed = UI.Embed(
            description=f"Added {member.mention} to {config.roles['helper']}")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")

        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @helper_admin.command(name="remove", aliases=["r", "rm"])
    @commands.has_role(config.roles['admin'])
    async def helper_remove(self, ctx, member: discord.Member):
        """removes a helper"""
        helper_role = get(member.guild.roles, name=config.roles['helper'])
        helper_ids = [helper.id for helper in helper_role.members]
        if member.id not in helper_ids:
            embed = UI.Embed(
                description=f"Member {member.mention} does not have role {config.roles['helper']}")
            embed.set_author(name=f"{ctx.author}",
                             icon_url=f"{ctx.author.avatar.url}")
            await ctx.channel.send(embed=embed)

            await ctx.message.delete()
            return

        await member.remove_roles(helper_role)
        db.delete_helper(member.id)

        embed = UI.Embed(
            description=f"Removed {member.mention} from role {config.roles['helper']}")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")
        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

    @helper_admin.command(name="refresh", aliases=["ref"])
    @commands.has_role(config.roles['admin'])
    async def helper_refresh(self, ctx):
        """refreshes helpers from the api"""
        embed = UI.Embed(
            description="sending requests...")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")

        message = await ctx.channel.send(embed=embed)
        await ctx.message.delete()

        try:
            await UpdateHelpers.main(self.bot)
        except exceptions.ChallengeDoesNotExist as e:
            embed.description = f"challenge id {e.args[0]} does not exist. getting new challenges..."
            await message.edit(embed=embed)
            asyncio.sleep(2)
            await ScrapeChallenges.main(self.bot)
        embed.description = "helpers refreshed"
        await message.edit(embed=embed)

    @helper_admin.command(name="update", aliases=["upd"])
    @commands.has_role(config.roles['admin'])
    async def helper_update(self, ctx, choice: str = "add"):
        """updates helpers to channels: add(default) or remove"""
        choice_ = choice
        try:
            choice = getattr(types.HelperSync, choice.upper())
        except AttributeError:
            return await ctx.channel.send("choice must be either add or remove")
        try:
            await UpdateHelpers.modify_helpers_to_channel(self.bot, choice=choice.value)
        except exceptions.HelperSyncError:
            pass

        choice_ = f"{choice_}ed all helpers to" if choice_[-1:
                                                           ] != 'e' else f"{choice_[:-1]}ed all helpers from"
        embed = UI.Embed(
            description=f"{choice_} all tickets")
        embed.set_author(name=f"{ctx.author}",
                         icon_url=f"{ctx.author.avatar.url}")
        await ctx.channel.send(embed=embed)

        await ctx.message.delete()

def setup(bot: commands.Bot):
    bot.add_cog(UtilityCommands(bot))
