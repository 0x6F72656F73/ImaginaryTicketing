import discord
from discord import ButtonStyle

import cogs.helpers.actions as actions

class CreateHelpButton(discord.ui.Button):  # add emoji
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        epicreactions = actions.Actions(
            interaction.guild, interaction.user, interaction.channel, 1234)
        ticket_channel = await epicreactions.create(type_=self.label)
        await interaction.response.send_message(f'You can view your ticket at {ticket_channel.mention}', ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreateHelpButton(
            label='help', style=ButtonStyle.primary, custom_id='ticketing:request_help'))
        self.add_item(CreateHelpButton(
            label='submit', style=ButtonStyle.success, custom_id='ticketing:request_submit'))
        self.add_item(CreateHelpButton(
            label='misc', style=ButtonStyle.danger, custom_id='ticketing:request_misc'))
