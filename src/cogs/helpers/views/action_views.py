import discord
from discord import ButtonStyle

import cogs.helpers.actions as actions

class ActionButton(discord.ui.Button):  # add emoji
    def __init__(self, label: str, style: ButtonStyle, custom_id: str, action: str, **kwargs):
        self.action = action
        self.kwargs = kwargs
        super().__init__(label=label, style=style, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        epicreactions = actions.Actions(
            interaction.guild, interaction.user, interaction.channel, 1234)
        await getattr(epicreactions, self.action)(type_=self.label, **self.kwargs)

class CloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ActionButton(
            label='close', style=ButtonStyle.primary, custom_id='ticketing:action_close', action='close'))

class ReopenDeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(ActionButton(
            label='reopen', style=ButtonStyle.primary, custom_id='ticketing:action_reopen', action='reopen'))

    @discord.ui.button(label='reopen', style=ButtonStyle.primary, custom_id='ticketing:action_reopen')
    async def reopen(self, button: discord.ui.Button, interaction: discord.Interaction):
        epicreactions = actions.Actions(
            interaction.guild, interaction.user, interaction.channel, 1234)
        await epicreactions.reopen()

    @discord.ui.button(label='delete', style=ButtonStyle.red, custom_id='ticketing:action_delete')
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        epicreactions = actions.Actions(
            interaction.guild, interaction.user, interaction.channel, 1234)
        await epicreactions.delete()

class DeleteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='delete', style=ButtonStyle.red, custom_id='ticketing:action_delete')
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        epicreactions = actions.Actions(
            interaction.guild, interaction.user, interaction.channel, 1234)
        await epicreactions.delete()
