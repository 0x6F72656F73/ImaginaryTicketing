import discord

from utils import types
class Options:
    """all options for different types of tickets"""

    @staticmethod
    def message(ticket_type: types.TicketType, moderator=None) -> str:
        """get the welcome message from the corresponding category

        Parameters
        ----------
        ticket_type : `types.TicketType`
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
Please send the challenge below in the following format and then create a thread off of your challenge message for discussion:

\*\*Title\*\* 
\*\*Category:\*\* 
\*\*Difficulty:\*\* 
\*\*Description:\*\* 
\*\*Flag:\*\* ||`hidden and inside` ``||
\*\*Player Attachments:\*\*
\*\*Admin Attachments:\*\* 
\*\*Solve idea/Writeup:\*\* ||hidden like this please||
""",
               "misc": f"""
Soon a {mention} member will assist you.
For now, you can start describing the issue so we can help you faster.
If you want to close this ticket, click on the :lock:""",
               }

        return msg[ticket_type]

    @staticmethod
    def limit(ticket_type: types.TicketType) -> int:
        """max number of tickets for someone

        Parameters
        ----------
        ticket_type : `types.TicketType`
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
    def full_category_name(ticket_type: types.TicketType) -> str:
        """get the category name of a ticket

        Parameters
        ----------
        ticket_type : `types.TicketType`
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
    def name_open(ticket_type: types.TicketType, count: int = None, user: discord.user.User = None) -> str:
        """gets the name of an opened ticket

        Parameters
        ----------
        ticket_type : `types.TicketType`
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
    def name_close(ticket_type: types.TicketType, count: int = None, user: discord.user.User = None) -> str:
        """gets the name of an closed ticket

        Parameters
        ----------
        ticket_type : `types.TicketType`
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
