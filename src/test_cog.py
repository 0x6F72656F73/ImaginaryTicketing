from discord import Embed
from discord_slash import SlashContext, ComponentContext
from discord_slash.cog_ext import cog_slash, cog_component
from discord.ext import commands

from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_select, create_select_option, create_actionrow

from cogs.helpers.actions import Actions

guild_ids = [788162899515801637, 861845094415728681]

class Slash(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def aa(self, ctx):
        await ctx.channel.send("a")

    @cog_slash(name="aaa", description="a pog command", guild_ids=guild_ids)
    async def _ping(self, ctx: SlashContext):
        options = [create_select_option(
            f"challenge {i}", value=f"challenge {i}") for i in range(1, 26)]
        select = create_select(
            options=options,
            placeholder="Please choose a challenge",
            max_values=1,  # the maximum number of options a user can select
            custom_id='testing')

        action_row = create_actionrow(select)

        await ctx.send(components=[action_row], content="a")

    @cog_component()
    async def testing(self, ctx: ComponentContext):
        print(ctx.selected_options)
        epicreactions = Actions(commands.Cog, self.bot,
                                ctx.guild, ctx.author, ctx.channel, 1234, False, 'a')
        print(epicreactions)
        await ctx.send('a')
        # await ctx.edit_origin(content=f"You selected {ctx.selected_options}")


def setup(bot):
    bot.add_cog(Slash(bot))
