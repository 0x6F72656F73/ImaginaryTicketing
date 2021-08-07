import sqlite3
import json
from itertools import chain
from typing import Union, List
import logging

from utils.others import Others

log = logging.getLogger(__name__)

class DatabaseManager():
    """Database Actions"""

    @classmethod
    def _db_connect(cls) -> sqlite3.Connection:
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
                WHERE channel_id=$1
                """
        values = (channel_id,)
        user_id = cls._raw_select(query, values, fetch_one=True)
        try:
            return int(user_id[0])
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None

    @classmethod
    def get_all_ticket_channel_messages(cls, guild_id: int) -> List[int]:
        """gets a list of all ticket message's ids for a guild

        Parameters
        ----------
        guild_id : `int`
            guild to get info from\n

        Returns
        -------
        `list[int]`: all ticket messages\n
        """
        query = "SELECT ticket_id FROM tickets WHERE guild_id = $1"
        values = (guild_id,)
        ticket_id_list = cls._raw_select(query, values, fetch_all=True)
        ticket_id_list = list(chain(*ticket_id_list))
        return ticket_id_list

    @classmethod
    def get_all_ticket_channels(cls, guild_id: int) -> List[int]:
        """gets a list of all ticket channels for a guild

        Parameters
        ----------
        guild_id : `int`
            guild to get info from\n

        Returns
        -------
        `list[int]`: all ticket channels
        """
        query = "SELECT channel_id FROM requests WHERE guild_id = $1"
        values = (guild_id,)
        db_ticket_channel_ids = cls._raw_select(query, values, fetch_all=True)
        ticket_channel_ids = list(chain(*db_ticket_channel_ids))
        return ticket_channel_ids

    @classmethod
    def get_status(cls, channel_id: int) -> str:
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
                WHERE channel_id = $1
                """
        values = (channel_id,)
        status = cls._raw_select(query, values, fetch_one=True)
        try:
            return status[0]
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None

    @classmethod
    def get_number_new(cls, ticket_type: int) -> str:
        """gets the number of tickets of that ticket type

        Parameters
        ----------
        ticket_type : `str`
            type of ticket\n

        Returns
        -------
        `str`: new number
        """
        query = """SELECT count(1) FROM
        (SELECT * FROM requests WHERE ticket_type=$1 
        union SELECT * FROM archive WHERE ticket_type=$1)
                """
        values = (ticket_type,)
        ret = cls._raw_select(query, values, fetch_one=True)
        try:
            return ret[0]
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None

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
        query = "SELECT channel_name FROM requests WHERE channel_id = $1"
        values = (channel_id,)
        db_channel_name_str = cls._raw_select(query, values, fetch_one=True)
        try:
            db_channel_name = db_channel_name_str[0].lower()
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None
        number = db_channel_name.split("-")[-1]
        return number

    @classmethod
    def get_ticket_type(cls, channel_id: int) -> str:
        """get the ticket type from the channel_id

        Parameters
        ----------
        channel_id : `int`
            the channel id\n
        Returns
        -------
        `str`: ticket type
        """
        query = "SELECT ticket_type FROM requests WHERE channel_id = $1"
        values = (channel_id,)
        ticket_type = cls._raw_select(query, values, fetch_one=True)
        try:
            return ticket_type[0]
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None

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
        query = "SELECT channel_name FROM requests WHERE channel_id = $1"
        values = (channel_id,)
        db_channel_name_str = cls._raw_select(query, values, fetch_one=True)
        try:
            return db_channel_name_str[0].lower()
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None

    @classmethod
    def update_status(cls, status: str, channel_id: int):
        """updates the status of a channel

        Parameters
        ----------
        status : `str`
            the new status\n
        channel_id : `int`
            the channel id\n
        """
        query = "UPDATE requests set status = $1 WHERE channel_id = $2"
        values = (status, channel_id,)
        cls._raw_update(query, values)

    @classmethod
    def get_check(cls, channel_id: int) -> int:
        """gets the check(status) if a channel has checked or not

        Parameters
        ----------
        channel_id : `int`
            the channel id\n

        Returns
        -------
        `str`: the check
        """
        query = "SELECT checked FROM requests WHERE channel_id=$1"
        values = (channel_id,)
        check = cls._raw_select(query, values, fetch_one=True)
        try:
            return int(check[0])
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None

    @classmethod
    def get_guild_check(cls, guild_id: int) -> str:
        """gets the check(status) if a channel has checked or not
        for every channel in the guild

        Parameters
        ----------
        guild_id : `int`
            the guild id\n

        Returns
        -------
        `str`: the check
        """
        query = "SELECT channel_id FROM requests WHERE guild_id=$1 and checked=2"
        values = (guild_id,)
        safe_tickets = cls._raw_select(query, values, fetch_all=True)
        return safe_tickets

    @classmethod
    def update_check(cls, check: str, channel_id: int):
        """gets the check(status) if a channel has checked or not

        Parameters
        ----------
        check : `str`
            the new check value\n
        channel_id : `int`
            the channel id\n
        """
        query = "UPDATE requests SET checked = $1 WHERE channel_id=$2"
        cls._raw_update(query, (check, channel_id))

    @classmethod
    def get_submit_check(cls, user_id: int) -> Union[str, None]:
        """checks if a user has a challenge submit ticket open

        Parameters
        ----------
        user_id : `int`
            the user to check for \n

        Returns
        -------
        `Union[str, None]`: the channel id if a ticket exists, None if no ticket exists
        """
        query = "SELECT channel_id FROM requests WHERE user_id=$1 AND ticket_type='submit' AND status='open'"
        values = (user_id,)
        check = cls._raw_select(query, values, fetch_one=True)
        try:
            return check[0]
        except TypeError:
            return None
        except Exception as exception:
            log.exception(exception)
            return None

    @classmethod
    def add_challenge(cls, id_: int, author: str, title: str, ignore: bool = False):
        query = "INSERT INTO challenges(id, author, title, ignore) VALUES($1,$2,$3,$4)"
        values = (id_, author, title, ignore)
        cls._raw_insert(query, values)

    @classmethod
    def get_all_challenges(cls):
        query = "SELECT * FROM challenges"
        all_challenges = cls._raw_select(query)
        return all_challenges

    @classmethod
    def get_challenge(cls, challenge_id: int):
        query = "SELECT * FROM challenges where id = $1"
        values = (challenge_id,)
        challenge = cls._raw_select(query, values, fetch_one=True)
        return challenge

    @classmethod
    def refresh_database(cls, challenges: List[Others.Challenge]):
        delete_query = "DELETE FROM challenges"
        cls._raw_delete(delete_query)
        insert_query = "INSERT INTO challenges(id, title, author, category, ignore) VALUES($1,$2,$3,$4,$5)"
        for id_, title, author, category, ignore, _ in challenges:
            values = (id_, title, author, category, ignore)
            cls._raw_insert(insert_query, values)

    @classmethod
    def update_helpers(cls, helper_id_list: List[int], challenge_id: int):
        helpers = json.dumps(helper_id_list)
        query = "UPDATE challenges SET helper_id_list = $1 WHERE id = $2"
        values = (helpers, challenge_id,)
        cls._raw_update(query, values)

    @classmethod
    def update_helper(cls, helper_id: int, challenge_id: int):
        challenge = Others.Challenge(*cls.get_challenge(challenge_id))
        helpers = []
        if challenge.helper_id_list:
            helpers = json.loads(challenge.helper_id_list)
        helpers.append(helper_id)
        helpers = json.dumps(list(set(helpers)))
        query = "UPDATE challenges SET helper_id_list = $1 WHERE id = $2"
        values = (helpers, challenge_id,)
        cls._raw_update(query, values)
