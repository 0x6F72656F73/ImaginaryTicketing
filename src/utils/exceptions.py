class MaxChannelTicketError(Exception):
    """Raised when the max number of tickets has been reached per category"""

class MaxUserTicketError(Exception):
    """Raised when the max number of tickets has been reached per user"""

class NoChallengeSelected(Exception):
    """Raised when no challenge is selected"""

class ChallengeDoesNotExist(Exception):
    """Raised when challenges solved by helpers don't exist"""
