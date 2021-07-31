from discord.ext import commands

from .action_views import CloseView, ReopenDeleteView, DeleteView
from .command_views import TicketView

def setup(bot: commands.Bot):
    for view in {CloseView, ReopenDeleteView, DeleteView}:
        bot.add_view(view())
    bot.add_view(TicketView(bot))
