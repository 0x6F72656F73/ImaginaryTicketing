import sqlite3
import json
from itertools import chain
from typing import Union, List
import logging

from utils import types
from utils.utility import Challenge
from utils import exceptions

log = logging.getLogger(__name__)

class DatabaseManager():
    """Database Actions"""

    @classmethod
    def _db_connect(cls) -> Union[sqlite3.Connection, None]:
        try:
            conn = sqlite3.connect('utils/database/bot.db')
            conn.row_factory = sqlite3.Row
        except Exception as e:
            log.exception(e)
            return None
        return conn

    @classmethod
    def _raw_insert(cls, query: str, *values):
        conn = cls._db_connect()
        cur = conn.cursor()
        try:
            with conn:
                cur.execute(query, *values)
        except Exception as e:
            log.exception(str(e))
        finally:
            conn.close()

    @classmethod
    def _raw_update(cls, query: str, *values):
        return cls._raw_insert(query, *values)

    @classmethod
    def _raw_delete(cls, query: str, *values):
        return cls._raw_insert(query, *values)

    @classmethod
    def _raw_select(cls, query: str, *values, fetch_one: bool = False, fetch_all: bool = True) -> Union[sqlite3.Row, list]:
        conn = cls._db_connect()
        cur = conn.cursor()
        ret = []
        try:
            with conn:
                cur.execute(query, *values)
                if fetch_one:
                    ret = cur.fetchone()
                elif fetch_all:
                    ret = cur.fetchall()
                else:
                    ret = cur.fetchall()
        except Exception as e:
            log.exception(str(e))
        finally:
            conn.close()
        return ret

    @classmethod
    def create_ticket(cls, channel_id: int, channel_name: str, guild_id: int, user_id: int, t_type: types.TicketType, status: types.TicketStatus, bg_check: types.TicketCheck):
        """create a ticket

        Parameters
        ----------
        channel_id : `int`
            the channel id\n
        channel_name : `str`
            the channel name\n
        guild_id : `int`
            the guild id\n
        user_id : `int`
            the user's id who created the ticket channel\n
        t_type : `types.TicketType`
            type of ticket\n
        status : `types.TicketStatus`
            status of ticket\n
        bg_check : `types.TicketCheck`
            whether the ticket is checked or not\n
        """
        query = """
        INSERT INTO requests(channel_id, channel_name, guild_id, user_id, t_type, status, bg_check) 
        VALUES ($1,$2,$3,$4,$5,$6,$8 )"""
        values = (channel_id, channel_name, guild_id,
                  user_id, t_type, status, bg_check,)
        cls._raw_insert(query, values)

    @classmethod
    def update_ticket_name(cls, channel_name: str, channel_id: int):
        """updates the name of a ticket

        Parameters
        ----------
        channel_name : `str`
            the channel's name\n
        channel_id : `int`
            the channel's id\n
        """
        query = """
        UPDATE requests 
        SET channel_name = $1 WHERE channel_id = $2"""
        values = (channel_name, channel_id,)
        cls._raw_update(query, values)

    @classmethod
    def delete_ticket(cls, channel_id: int):
        """deletes a ticket

        Parameters
        ----------
        channel_id : `int`
            the channel's id_\n
        """
        query = """
        DELETE FROM requests
        WHERE channel_id = $1
        """
        values = (channel_id,)
        cls._raw_delete(query, values)

    @classmethod
    def move_ticket_to_archive(cls, channel_id: int):
        """moves the ticket from requests to archive table

        Parameters
        ----------
        channel_id : `int`
            the channel's id_\n
        """
        query = """
        INSERT INTO archive
        SELECT * FROM requests
        WHERE channel_id = $1
        """
        values = (channel_id,)
        cls._raw_insert(query, values)

    @classmethod
    def get_user_id(cls, channel_id: int) -> Union[int, None]:
        """gets the id of a user

        Parameters
        ----------
        channel_id : `int`
            the channel id\n

        Returns
        -------
        `int`: the user's id
        """

        query = """
        SELECT user_id FROM requests
        WHERE channel_id = $1"""
        values = (channel_id,)
        user_id = cls._raw_select(query, values, fetch_one=True)
        try:
            return int(user_id[0])
        except TypeError as e:
            raise ValueError(
                f"No channel exists with id {channel_id}") from e

    @classmethod
    def get_all_help_channels(cls, guild_id: int) -> List[int]:
        """gets a list of all help ticket channels for a guild

        Parameters
        ----------
        guild_id : `int`
            guild to get tickets from\n

        Returns
        -------
        `List[int]`: all help ticket channels
        """
        query = """
        SELECT channel_id FROM requests 
        WHERE t_type='help' AND guild_id = $1"""
        values = (guild_id,)
        db_ticket_channel_ids = cls._raw_select(query, values, fetch_all=True)
        return list(chain(*db_ticket_channel_ids))

    @classmethod
    def get_status(cls, channel_id: int) -> types.TicketStatus:
        """gets the current status of a channel

        Parameters
        ----------
        channel_id : `int`
            the channel id\n

        Returns
        -------
        `str`: the channel's status
        """
        query = """
        SELECT status FROM requests
        WHERE channel_id = $1"""
        values = (channel_id,)
        status = cls._raw_select(query, values, fetch_one=True)
        try:
            return status[0]
        except TypeError as e:
            raise ValueError(
                f"No channel exists with id {channel_id}") from e

    @classmethod
    def get_tickets_per_user(cls, t_type: types.TicketType, user_id: int):
        """gets the total number of open tickets for a user

        Parameters
        ----------
        t_type : `types.TicketType`
            the type of ticket\n
        user_id : `int`
            the user's id\n

        Returns
        -------
        `str`: the number of undeleted tickets
        """
        query = """
        SELECT count(1) FROM 
        (SELECT * FROM requests 
        WHERE t_type=$1 and user_id=$2)"""
        values = (t_type, user_id,)
        n_tickets = cls._raw_select(query, values, fetch_one=True)
        return n_tickets[0]

    @classmethod
    def get_number_new(cls, t_type: types.TicketType) -> int:
        """gets the number of tickets of that ticket type

        Parameters
        ----------
        t_type : `types.TicketType`
            type of ticket\n

        Returns
        -------
        `int`: new number
        """
        query = """
        SELECT count(1) FROM
        (SELECT * FROM requests WHERE t_type=$1
        union SELECT * FROM archive WHERE t_type=$1)"""
        values = (t_type,)
        ret = cls._raw_select(query, values, fetch_one=True)
        return int(ret[0])

    @classmethod
    def get_number_previous(cls, channel_id: int) -> str:
        """gets the number of tickets of that ticket type

        Parameters
        ----------
        channel_id : `int`
            the channel id\n

        Returns
        -------
        `str`: previous number
        """
        query = """
        SELECT channel_name FROM requests 
        WHERE channel_id = $1"""
        values = (channel_id,)
        db_channel_name_str = cls._raw_select(query, values, fetch_one=True)
        try:
            db_channel_name = db_channel_name_str[0].lower()
        except TypeError as e:
            raise ValueError(
                f"No channel exists with id {channel_id}") from e
        number = db_channel_name.split("-")[-1]
        return number

    @classmethod
    def get_ticket_type(cls, channel_id: int) -> types.TicketType:
        """get the ticket type from the channel_id

        Parameters
        ----------
        channel_id : `int`
            the channel id\n
        Returns
        -------
        `types.TicketType`: ticket type
        """
        query = """
        SELECT t_type FROM requests 
        WHERE channel_id = $1"""
        values = (channel_id,)
        t_type = cls._raw_select(query, values, fetch_one=True)
        try:
            return t_type[0]
        except TypeError as e:
            raise ValueError(
                f"No channel exists with id {channel_id}") from e

    @classmethod
    def get_channel_name(cls, channel_id: int) -> str:
        """get the channel name from the channel_id

        Parameters
        ----------
        channel_id : `int`
            the channel id\n
        Returns
        -------
        `str`: the channel name
        """
        query = """
        SELECT channel_name FROM requests 
        WHERE channel_id = $1"""
        values = (channel_id,)
        db_channel_name_str = cls._raw_select(query, values, fetch_one=True)
        try:
            return db_channel_name_str[0].lower()
        except TypeError as e:
            raise ValueError(
                f"No channel exists with id {channel_id}") from e

    @classmethod
    def update_status(cls, status: types.TicketStatus, channel_id: int):
        """updates the status of a channel

        Parameters
        ----------
        status : `types.TicketStatus`
            the new status\n
        channel_id : `int`
            the channel id\n
        """
        query = """UPDATE requests
        SET status = $1 WHERE channel_id = $2"""
        values = (status, channel_id,)
        cls._raw_update(query, values)

    @classmethod
    def get_check(cls, channel_id: int) -> types.TicketCheck:
        """gets the bg_check for autoclose

        Parameters
        ----------
        channel_id : `int`
            the channel id\n

        Returns
        -------
        `int(types.TicketCheck)`: the bg_check
        """
        query = """
        SELECT bg_check FROM requests 
        WHERE channel_id = $1"""
        values = (channel_id,)
        bg_check = cls._raw_select(query, values, fetch_one=True)
        try:
            return bg_check[0]
        except TypeError as e:
            raise ValueError(
                f"No channel exists with id {channel_id}") from e

    @classmethod
    def update_check(cls, bg_check: types.TicketCheck, channel_id: int):
        """gets the bg_check for a channel

        Parameters
        ----------
        bg_check : `types.TicketCheck`
            the new bg_check value\n
        channel_id : `int`
            the channel id\n
        """
        query = """
        UPDATE requests
        SET bg_check = $1 WHERE channel_id = $2"""
        cls._raw_update(query, (bg_check, channel_id))

    @classmethod
    def get_guild_safe_tickets(cls, guild_id: int) -> List[str]:
        """if a channel's bg_check is 2, returns the channel_id
        for every channel in the guild

        Parameters
        ----------
        guild_id : `int`
            the guild id\n

        Returns
        -------
        `List[str]`: list of safe tickets
        """
        query = """
        SELECT channel_id FROM requests 
        WHERE guild_id=$1 and bg_check =2"""
        values = (guild_id,)
        safe_tickets = cls._raw_select(query, values, fetch_all=True)
        return list(chain(*safe_tickets))

    @classmethod
    def get_all_challenges(cls) -> List[sqlite3.Row]:
        query = "SELECT * FROM challenges"
        all_challenges = cls._raw_select(query)
        return all_challenges

    @classmethod
    def get_challenge_from_id(cls, challenge_id: int):
        query = """
        SELECT * FROM challenges 
        WHERE id = $1"""
        values = (challenge_id,)
        challenge = cls._raw_select(query, values, fetch_one=True)
        return challenge

    @classmethod
    def get_helpers_from_title(cls, title: str):
        query = """
        SELECT helper_id_list FROM challenges 
        WHERE title = $1"""
        values = (title, )
        return cls._raw_select(query, values, fetch_one=True)

    @classmethod
    def refresh_database_ch(cls, challenges: List[Challenge]):
        delete_query = "DELETE FROM challenges"
        cls._raw_delete(delete_query)
        insert_query = """
        INSERT INTO challenges(id, title, author, category, ignore, helper_id_list)
        VALUES($1,$2,$3,$4,$5,$6)"""
        for id_, title, author, category, ignore, _ in challenges:
            values = (id_, title, author, category, ignore, str([]))
            cls._raw_insert(insert_query, values)

        # all_helpers = {guild.get_member_named(ch.author) for ch in challenges}

    @classmethod
    def update_helpers_ch(cls, helper_id_list: List[int], challenge_id: int):
        helpers = json.dumps(helper_id_list)
        query = """
        UPDATE challenges
        SET helper_id_list = $1 WHERE id = $2"""
        values = (helpers, challenge_id,)
        cls._raw_update(query, values)

    @classmethod
    def update_helper_ch(cls, helper_id: int, challenge_id: int):
        challenge = cls.get_challenge_from_id(challenge_id)
        if challenge is None:
            raise exceptions.ChallengeDoesNotExist(challenge_id)
        challenge = Challenge(*challenge)

        helpers = json.loads(challenge.helper_id_list)
        helpers.append(helper_id)
        helpers = json.dumps(list(set(helpers)))
        query = """
        UPDATE challenges
        SET helper_id_list = $1 WHERE id = $2"""
        values = (helpers, challenge_id,)
        cls._raw_update(query, values)

    @classmethod
    def create_helper(cls, discord_id: int):
        query = """
        INSERT INTO helpers(discord_id, is_available) 
        VALUES($1,$2)"""
        values = (discord_id, "1",)
        cls._raw_update(query, values)

    @classmethod
    def delete_helper(cls, discord_id: int):
        query = """
        DELETE FROM helpers
        WHERE discord_id = $1"""
        values = (str(discord_id),)
        cls._raw_delete(query, values)

    @classmethod
    def update_helper_status(cls, status: types.HelperAvailable, discord_id: int):
        query = """
        UPDATE helpers
        SET is_available = $1 WHERE discord_id = $2"""
        values = (status, discord_id,)
        cls._raw_update(query, values)

    @classmethod
    def get_helper_status(cls, discord_id: int):
        query = """
        SELECT is_available FROM helpers
        WHERE discord_id = $1"""
        values = (discord_id,)
        status = cls._raw_select(query, values, fetch_one=True)
        try:
            if status[0] == 1:
                return True
            return False
        except TypeError as e:
            raise ValueError(
                f"No helper exists with id {discord_id}") from e
