class MaxChannelTicketError(Exception):
    """Raised when the max number of tickets has been reached per category"""
    pass

class MaxUserTicketError(Exception):
    """Raised when the max number of tickets has been reached per user"""
    pass

class NoChallengeSelected(Exception):
    """Raised when no challenge is selected"""
    pass
