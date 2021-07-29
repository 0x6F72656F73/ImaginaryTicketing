class MaxChannelTicketError(Exception):
    """Raised when the max number of tickets has been reached per category"""

class MaxUserTicketError(Exception):
    """Raised when the max number of tickets has been reached per user"""

class NoChallengeSelected(Exception):
    """Raised when no challenge is selected"""
