import asyncio
from collections import defaultdict
import json
from typing import Optional, Dict, Union
import logging

import discord
from discord.ext import commands
from discord.utils import get

import config

from utils.database.db import DatabaseManager as db
from utils.background import ScrapeChallenges, UpdateHelpers
from utils.utility import Utility, UI, Challenge
from utils import exceptions

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
        message = await ctx.send(f'Purged {limit} messages')
        await asyncio.sleep(3)
        try:
            await message.delete()
        except discord.errors.NotFound:
            pass

    @commands.command(name="check")
    @commands.has_role(config.roles['admin'])
    async def check_discord(self, ctx):
        """Checks if all configurations are valid"""
        bot_in_guild = ctx.guild.get_member(self.bot.user.id)
        checks = Utility.check_discord(bot_in_guild, ctx.guild)

        embed = UI.Embed(title="Checks")
        UI.add_to_description(embed, "**Successful checks:**")
        for check in checks['pass']:
            UI.add_to_description(embed, f"- {check}")

        UI.add_to_description(embed, "**Failed checks:**")
        for check in checks['fail']:
            UI.add_to_description(embed, f"- {check}")

        await ctx.channel.send(embed=embed)

    @commands.group(name="challenge", aliases=["c", "chall"], invoke_without_command=True)
    @commands.has_role(config.roles['admin'])
    async def challenge(self, ctx):
        """Base challenge command. Shows stats on challenges."""
        embed = UI.Embed(title="Challenges")
        print(type(db.get_all_challenges()))
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

    @challenge.command(name="refresh", aliases=["ref"])
    @commands.has_role(config.roles['admin'])
    async def refresh(self, ctx):
        """refreshes challenges from the api"""
        embed = UI.Embed(
            description="sending requests...")
        message = await ctx.channel.send(embed=embed)

        await ScrapeChallenges.main(self.bot)

        embed.description = "challenges refreshed"
        await message.edit(embed=embed)

    @commands.group(name="helperadmin", aliases=["ha"], invoke_without_command=True)
    @commands.has_role(config.roles['admin'])
    async def helper_admin(self, ctx):
        """Base helper-admin command. Shows stats on helpers."""
        helper_role = get(ctx.guild.roles, name=config.roles['helper'])
        if len(helper_role.members):
            helpers = '\n'.join(
                [member.mention for member in helper_role.members])
        else:
            helpers = 'No helpers'

        embed = UI.Embed(
            title=f"{config.roles['helper']}", description=helpers)
        await ctx.channel.send(embed=embed)

    @helper_admin.command(name="add", aliases=["a"])
    @commands.has_role(config.roles['admin'])
    async def helper_add(self, ctx, member: discord.Member):
        """adds a helper"""
        helper_role = get(member.guild.roles, name=config.roles['helper'])
        helper_ids = [helper.id for helper in helper_role.members]
        if member.id in helper_ids:
            embed = UI.Embed(
                description=f"Member {member.mention} already has role {config.roles['helper']}")
            await ctx.channel.send(embed=embed)
            return

        await member.add_roles(helper_role)
        embed = UI.Embed(
            description=f"Added {member.mention} to role {config.roles['helper']}")
        await ctx.channel.send(embed=embed)

    @helper_admin.command(name="remove", aliases=["r", "rm"])
    @commands.has_role(config.roles['admin'])
    async def helper_remove(self, ctx, member: discord.Member):
        """removes a helper"""
        helper_role = get(member.guild.roles, name=config.roles['helper'])
        helper_ids = [helper.id for helper in helper_role.members]
        if member.id not in helper_ids:
            embed = UI.Embed(
                description=f"Member {member.mention} does not have role {config.roles['helper']}")
            await ctx.channel.send(embed=embed)
            return
        await member.remove_roles(helper_role)
        embed = UI.Embed(
            description=f"Removed {member.mention} from role {config.roles['helper']}")
        await ctx.channel.send(embed=embed)

    @helper_admin.command(name="refresh", aliases=["ref"])
    @commands.has_role(config.roles['admin'])
    async def helper_refresh(self, ctx):
        """refreshes helpers from the api"""
        embed = UI.Embed(
            description="sending requests...")
        message = await ctx.channel.send(embed=embed)
        try:
            await UpdateHelpers.main(self.bot)
        except exceptions.ChallengeDoesNotExist as e:
            embed.description = f"challenge id {e.args[0]} does not exist. getting new challenges..."
            await message.edit(embed=embed)
            await ScrapeChallenges.main(self.bot)
        embed.description = "helpers refreshed"
        await message.edit(embed=embed)

    @helper_admin.command(name="update", aliases=["upd"])
    @commands.has_role(config.roles['admin'])
    async def helper_update(self, ctx):
        """updates helpers to channels"""
        await UpdateHelpers.add_helpers(self.bot)
        embed = UI.Embed(
            description="helpers updated")
        await ctx.channel.send(embed=embed)

    # @commands.group(name="helperuser", aliases=["hu"], invoke_without_command=True)
    # async def helper_user(self, ctx):
    #     """Base helper-user command. Shows stats on helpers."""
    #     helper_role = get(ctx.guild.roles, name=config.roles['helper'])
    #     if len(helper_role.members):
    #         helpers = '\n'.join(
    #             [member.mention for member in helper_role.members])
    #     else:
    #         helpers = 'No helpers'

    #     embed = UI.Embed(
    #         title=f"{config.roles['helper']}", description=helpers)
    #     await ctx.channel.send(embed=embed)

    # @helper_user.command(name="status", aliases=["upd"])
    # # add custom check if has role or in table
    # async def helper_change_status(self, ctx, choice: Optional[bool]):
    #     """changes a helper to on or off """
    #     if not choice
    #     await UpdateHelpers.add_helpers(self.bot)
    #     embed = UI.Embed(
    #         description="helpers updated")
    #     await ctx.channel.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(UtilityCommands(bot))
