import textwrap

from discord import Embed
from discord_slash import SlashContext, ComponentContext
from discord_slash.cog_ext import cog_slash, cog_component
from discord.ext import commands

from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow

from cogs.helpers.actions import Actions
from utils.database.db import DatabaseManager as db
from utils.others import Others

guild_ids = [788162899515801637, 861845094415728681]

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def aa(self, ctx):
        await ctx.channel.send("a")

    @cog_slash(name="aaa", description="a pog command", guild_ids=guild_ids)
    async def _ping(self, ctx: SlashContext):
        challenges = [Others.Challenge(*list(challenge))
                      for challenge in db.get_all_challenges()]
        categories = {}
        for idx, chall in enumerate(challenges):
            if chall.category not in categories.values():
                print(f'going to add {chall.category}')
                categories[idx] = chall.category

        # categories = {"Crypto": 1, "Web": 2, "Pwn": 3, "Rev": 4, "Misc": 5}
        print(categories)
        # list_categories = list(categories)
        # challenges = [Others.Challenge(
        #     i, f"chall{i}", f"author{i}", list_categories[i % len(categories)], i % 3 == 0) for i in range(24)]
        if len(challenges) < 25:
            options = [create_select_option(
                label=textwrap.shorten(challenge.title, 25, placeholder='...'), value=f"{challenge.id_}") for challenge in challenges]
            select = create_select(
                options=options,
                placeholder="Please choose a challenge",
                max_values=1,
                custom_id='testing')

            action_row = create_actionrow(select)
            await ctx.send(components=[action_row], content="challenge selection")
        else:
            category_options = [create_select_option(
                label=category, value=f"{idx}") for idx, category in categories.items()]
            print(category_options)

        # if len<25, jes do one selct for that. if not, ask for actegroy, than use namedtuple to query forthat, then do selct fortitle of chall
        # print(second_options)

        # if second_options:
        #     second_select = create_select(
        #         options=second_options,
        #         placeholder="Please choose a challenge",
        #         max_values=1,
        #         custom_id='testing2')

        #     second_action_row = create_actionrow(second_select)
        #     await ctx.send(components=[second_action_row], content="challenge selection 2")

    # @cog_component()
    # async def testing(self, ctx: ComponentContext):
    #     print(ctx.selected_options[0])
    #     epicreactions = Actions(commands.Cog, self.bot,
    #                             ctx.guild, ctx.author, ctx.channel, 1234)
    #     await epicreactions.create(challenge=ctx.selected_options[0])
    #     await ctx.edit_origin(components=None)


def setup(bot):
    bot.add_cog(Slash(bot))
