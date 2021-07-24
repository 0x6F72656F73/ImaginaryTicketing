from discord import ButtonStyle
import discord

from cogs.helpers.actions import Actions

__all__ = ["TicketView"]

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='help', style=ButtonStyle.primary, custom_id='ticketing:request_help')
    async def green(self, button: discord.ui.Button, interaction: discord.Interaction):
        epicreactions = Actions(
            interaction.guild, interaction.user, interaction.channel, 1234)
        await epicreactions.create(type_='help')

    @discord.ui.button(label='submit', style=ButtonStyle.success, custom_id='ticketing:request_submit')
    async def red(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is red.', ephemeral=True)

    @discord.ui.button(label='misc', style=ButtonStyle.danger, custom_id='ticketing:request_misc')
    async def grey(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.response.send_message('This is grey.', ephemeral=True)
