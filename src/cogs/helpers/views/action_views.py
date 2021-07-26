import discord
from discord import ButtonStyle

import cogs.helpers.actions as actions

class ActionButton(discord.ui.Button):  # add emoji
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        ticket_action = getattr(
            actions, f"{self.custom_id.split('_')[1].capitalize()}Ticket")(interaction.guild, interaction.user, interaction.channel)
        await ticket_action.main()

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ActionButton(
            label='close', style=ButtonStyle.primary, custom_id='ticketing:action_close'))

class ReopenDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ActionButton(
            label='reopen', style=ButtonStyle.primary, custom_id='ticketing:action_reopen'))
        self.add_item(ActionButton(
            label='delete', style=ButtonStyle.red, custom_id='ticketing:action_delete'))

class DeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ActionButton(
            label='delete', style=ButtonStyle.red, custom_id='ticketing:action_delete'))
