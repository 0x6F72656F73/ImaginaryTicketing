# look for ebtter name in gh bots

import discord
from discord.ext import commands
import aiocron


from utils.background import AutoClose

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # @aiocron.crontab("* * * * * */10")
        # # @aiocron.crontab("0 * * * *")
        # async def start_auto_close():
        #     # await AutoClose.inactivity(self.bot, hours=48)
        #     await AutoClose.inactivity(self.bot, seconds=6)


def setup(bot):
    bot.add_cog(Tasks(bot))
