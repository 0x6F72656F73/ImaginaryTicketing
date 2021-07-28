from discord.ext import commands
import discord


class Select(discord.ui.Select):
    def __init__(self):
        super().__init__(custom_id="Some identifier", placeholder="Placeholder", min_values=1,
                         max_values=1, options=[discord.SelectOption(label="Hello", emoji="😳")])

    async def callback(self, interaction: discord.Interaction):
        # to get the selected options, you can use interaction.data
        await interaction.response.send_message("Hello", ephemeral=True)


class PersistentViewBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or('!'))
        self.persistent_views_added = False

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


bot = PersistentViewBot()


@bot.command()
async def test(ctx: commands.Context):
    view = discord.ui.View()
    view.add_item(Select())

    await ctx.send('Test', view=view)


bot.run('ODM5NjM0MTAxNDgwMzI1MjEw.YJMgMQ.a4xlyjoWHAiCV_5-OPusFX5FRFw')
