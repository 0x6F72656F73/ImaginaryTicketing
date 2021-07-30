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

        @aiocron.crontab("* * * * * */10")
        # @aiocron.crontab("0 * * * *")
        async def start_scraping_challenges():
            ScrapeChallenges.main()

        # @aiocron.crontab("* * * * * */10")
        # # @aiocron.crontab("* * * * 10 *")
        # async def start_adding_users():  # better name lol
        #     ScrapeChallenges.main()  # another class

def setup(bot):
    bot.add_cog(Tasks(bot))
