import discord

class Options:
    """all options for different types of tickets"""

    @staticmethod
    def message(ticket_type, moderator=None):
        """get the message from the corresponding category

        Parameters
        ----------
        ticket_type : `str`
            type of ticket\n
        moderator : `discord.role.Role`, `optional`
            moderator role, by default None\n
        """
        mention = None
        if moderator is None:
            mention = moderator
        else:
            mention = moderator.mention
        msg = {"help": f"""
Soon a {mention} member will assist you.
If you don't need help anymore, or you want to close this ticket, click on the :lock:""",
               "submit": """
Please create a thread for each challenge, and in the following format:

\*\*Title\*\* 
\*\*Category:\*\* 
\*\*Difficulty:\*\* 
\*\*Description:\*\* 
\*\*Flag:\*\* ``
\*\*Player Attachments:\*\*
\*\*Admin Attachments:\*\* 
\*\*Solve idea/Writeup:\*\* ||||
""",
               "misc": f"""
Soon a {mention} member will assist you.
For now, you can start telling us what the issue is so that we can help you faster.
If you want to close this ticket, click on the :lock:""",
               }

        return msg[ticket_type]

    @staticmethod
    def limit(ticket_type: str) -> int:
        """max number of tickets for someone

        Parameters
        ----------
        ticket_type : `str`
            ticket type\n

        Returns
        -------
        `int`: number of tickets
        """
        msg = {"help": 3,
               "submit": 2,
               "misc": 2}
        return msg[ticket_type]

    @staticmethod
    def full_category_name(ticket_type: str) -> str:
        """get the category name of a ticket

        Parameters
        ----------
        ticket_type : `str`
            Ticket type\n

        Returns
        -------
        `str`: full ticket type
        """
        msg = {"help": "support tickets",
               "submit": "challenge submissions",
               "misc": "support tickets"}
        return msg[ticket_type]

    @staticmethod
    def name_open(ticket_type: str, count: int = None, user: discord.user.User = None) -> str:
        """gets the name of an opened ticket

        Parameters
        ----------
        ticket_type : `str`
            Ticket Type\n
        count : `int`, `optional`
            ticket number, by default None\n
        user : `discord.user.User`, `optional`
            ticket user, by default None\n

        Returns
        -------
        `str`: opened ticket name
        """
        msg = {"help": f"help-{user.name}-{count}",
               "submit": f"challenge-{user.name}",
               "misc": f"misc-{user.name}-{count}", }

        return msg[ticket_type]

    @staticmethod
    def name_close(ticket_type: str, count: int = None, user: discord.user.User = None) -> str:
        """gets the name of an closed ticket

        Parameters
        ----------
        ticket_type : `str`
            Ticket Type\n
        count : `int`, `optional`
            ticket number, by default None\n
        user : `discord.user.User`, `optional`
            ticket user, by default None\n

        Returns
        -------
        `str` : closed ticket name
        """
        msg = {"help": f"help-closed-{user.name}-{count}",
               "submit": f"challenge-{user.name}-closed",
               "misc": f"misc-{user.name}-closed-{count}", }

        return msg[ticket_type]
