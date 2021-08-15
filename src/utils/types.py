from typing import Literal

TicketType = Literal["help", "submit", "misc"]
TicketStatus = Literal["open", "closed"]
TicketCheck = Literal["0", "1", "2"]

HelperAvailable = Literal["0", "1"]

#other stuff, look esp in db.py and actions.py
