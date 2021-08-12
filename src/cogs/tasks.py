from discord.ext import commands
import aiocron

from utils.background import AutoClose, ScrapeChallenges, UpdateHelpers
from utils import exceptions

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # @aiocron.crontab("* * * * * */10")
        @aiocron.crontab("0 * * * *")
        async def start_auto_close():
            await AutoClose.main(self.bot, hours=48)
            # await AutoClose.main(self.bot, seconds=2)

        @aiocron.crontab("0 9 * * *")
        async def start_scraping_challenges_9():
            await ScrapeChallenges.main(self.bot)

        @aiocron.crontab("30 9 * * *")
        async def start_scraping_challenges_9_30():
            await ScrapeChallenges.main(self.bot)

        @aiocron.crontab("0 */2 * * *")
        async def start_scraping_challenges_2_hours():
            await ScrapeChallenges.main(self.bot)

        # @aiocron.crontab("*/10 * * *")
        # @aiocron.crontab("* * * * * */10")
        async def start_adding_users():
            try:
                await UpdateHelpers.main(self.bot)
            except exceptions.ChallengeDoesNotExist:
                await ScrapeChallenges.main(self.bot)


def setup(bot):
    bot.add_cog(Tasks(bot))
