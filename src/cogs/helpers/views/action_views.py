from typing import List

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
            label='close', style=ButtonStyle.success, emoji='🔒', custom_id='ticketing:action_close'))

class ReopenDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ActionButton(
            label='reopen', style=ButtonStyle.primary, emoji='🔓', custom_id='ticketing:action_reopen'))
        self.add_item(ActionButton(
            label='delete', style=ButtonStyle.red, emoji='⛔', custom_id='ticketing:action_delete'))

class DeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ActionButton(
            label='delete', style=ButtonStyle.red, emoji='⛔', custom_id='ticketing:action_delete'))


class ChallengeSelect(discord.ui.Select['ChallengeView']):
    def __init__(self, custom_id: str, options: List[discord.SelectOption], placeholder: str):
        super().__init__(custom_id=custom_id,
                         placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.message.delete()
        view = self.view  # pylint: disable=maybe-no-member
        view.stop()

class ChallengeView(discord.ui.View):
    def __init__(self, author: discord.Member, custom_id: str, options: List[discord.SelectOption], placeholder: str, timeout: float = 300, **kwargs):
        super().__init__(timeout=timeout, **kwargs)
        self.add_item(ChallengeSelect(
            custom_id, options, placeholder))
        self.author = author

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user == self.author:
            return True
        await interaction.response.send_message("You're not allowed to choose", ephemeral=True)
        return False
