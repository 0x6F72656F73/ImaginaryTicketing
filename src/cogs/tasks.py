from discord.ext import commands
import aiocron

from utils.background import AutoClose
from utils.background import ScrapeChallenges
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
            ScrapeChallenges.main()

        @aiocron.crontab("30 9 * * *")
        async def start_scraping_challenges_9_30():
            ScrapeChallenges.main()

        @aiocron.crontab("0 */2 * * *")
        async def start_scraping_challenges_2_hours():
            ScrapeChallenges.main()

        # @aiocron.crontab("* * * * * */10")
        # # @aiocron.crontab("* * * * 10 *")
        # async def start_adding_users():  # better name lol
        #     ScrapeChallenges.main()  # another class

def setup(bot):
    bot.add_cog(Tasks(bot))
