import logging

import discord
from discord.ext import commands
# from discord.ext.forms import Form, ReactionForm

import config
from utils.others import Others
from utils.database.db import DatabaseManager as db

log = logging.getLogger(__name__)

class Submit(commands.Cog):
    """other useful commands"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # @commands.dm_only()
    # @commands.command(name="submit", aliases=["s"])
    # async def submit(self, ctx):
    #     CHECK = db.get_submit_check(ctx.author.id)
    #     if CHECK is None:
    #         await ctx.channel.send("Please create a challenge submission ticket before submitting a challenge")
    #         return

    #     await ctx.send("make sure you submit all challenges in the format specified in LINK ")
    #     form = Form(ctx, 'Challenge Submission')
    #     form.enable_cancelkeywords(False)

    #     form.set_timeout(5)

    #     await form.set_color("#66FFFF")  # Set the color of the form's embeds

    #     chall_questions = {'title': 'title',
    #                        'category': 'category',
    #                        'difficulty': 'difficulty',
    #                        'description': 'description',
    #                        'player_attachments (bit.ly link)': 'player_attachments',
    #                        'admin_attachments (bit.ly link)': 'admin_attachments',
    #                        'general_solve': 'general_solve',
    #                        'hosting_comments': 'hosting_comments',
    #                        'flag': 'flag'}

    #     for k, v in chall_questions.items():
    #         form.add_question(k, v)

    #     chall_raw = await form.start()  # Run the form!
    #     if chall_raw is None:
    #         await ctx.send("all required paremeters were not fulfilled")
    #         return

    #     chall_attrs = (vars(chall_raw))
    #     embed = discord.Embed(
    #         title=f"{chall_attrs['title']}", color=0xFF6666)

    #     full_parts = []
    #     for k, v in chall_attrs.items():
    #         if k == 'title':
    #             continue
    #         full_parts.append(f"**{k}**: {v}\n")
    #         if(k == "player_attachments" or k == "admin_attachments") and v == "":
    #             await ctx.send("all required options were not fulfilled")
    #             return
    #     full = "".join(full_parts)
    #     embed.description = full
    #     await ctx.send(embed=embed)
    #     to_send = tuple(chall_attrs.values())
    #     to_send = (ctx.author.id,) + to_send
    #     print(to_send)
    #     db.put_challenge(to_send)

    # @commands.command(name="getall", aliases=["ga"])
    # async def getall(self, ctx):
    #     challenges = db.get_challenge()
    #     print(challenges)

    @commands.command(name="say")
    async def say(self, ctx, *, message):
        """says a message through a webhook"""

        await Others.say_in_webhook(ctx.author, ctx.channel, ctx.author.avatar_url, False, message)
        await ctx.message.delete()

    @commands.command(name="saymember", aliases=["saym"])
    @commands.has_role(config.ADMIN_ROLE)
    async def saymember(self, ctx, member: discord.User, *, message):
        """says a message through a webhook from the specified *user*"""

        await Others.say_in_webhook(member, ctx.channel, member.avatar_url, False, message)
        await ctx.message.delete()

def setup(bot: commands.Bot):
    bot.add_cog(Submit(bot))
