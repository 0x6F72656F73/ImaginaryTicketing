from typing import Literal
from enum import Enum

TicketType = Literal["help", "submit", "misc"]
TicketStatus = Literal["open", "closed"]
TicketCheck = Literal["0", "1", "2"]

HelperAvailable = Literal[0, 1]

class HelperSync(Enum):
    ADD = True
    REMOVE = False
