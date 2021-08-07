import discord
from discord.ext import commands
from discord import ButtonStyle

import cogs.helpers.actions as actions
from utils import exceptions
import config
class CreateHelpButton(discord.ui.Button['TicketView']):  # add emoji
    def __init__(self, bot: commands.Bot, **kwargs):
        self.bot = bot
        super().__init__(**kwargs)

    async def callback(self, interaction: discord.Interaction):
        create_ticket = actions.CreateTicket(self.bot, self.label, interaction,
                                             interaction.guild, interaction.user, interaction.channel)
        try:
            await create_ticket.main()
        except (exceptions.MaxUserTicketError, exceptions.MaxChannelTicketError, discord.errors.NotFound):
            pass

class TicketView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        emoji_list = config.EMOJIS_MESSAGE
        self.add_item(CreateHelpButton(bot,
                                       label='help', style=ButtonStyle.primary, emoji=emoji_list[0], custom_id='ticketing:request_help'))
        self.add_item(CreateHelpButton(bot,
                                       label='misc', style=ButtonStyle.danger, emoji=emoji_list[2], custom_id='ticketing:request_misc'))
        self.add_item(CreateHelpButton(bot,
                                       label='submit', style=ButtonStyle.success, emoji=emoji_list[1], custom_id='ticketing:request_submit'))
