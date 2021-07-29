import discord
from discord import ButtonStyle

import cogs.helpers.actions as actions
import utils.exceptions as exceptions
class CreateHelpButton(discord.ui.Button):  # add emoji
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        create_ticket = actions.CreateTicket(self.label, interaction,
                                             interaction.guild, interaction.user, interaction.channel)
        try:
            await create_ticket.main()
        except (exceptions.MaxUserTicketError, exceptions.MaxChannelTicketError):
            pass

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CreateHelpButton(
            label='help', style=ButtonStyle.primary, custom_id='ticketing:request_help'))
        self.add_item(CreateHelpButton(
            label='submit', style=ButtonStyle.success, custom_id='ticketing:request_submit'))
        self.add_item(CreateHelpButton(
            label='misc', style=ButtonStyle.danger, custom_id='ticketing:request_misc'))
