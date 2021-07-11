import requests
from dotenv import dotenv_values
import textwrap
from utils.database.db import DatabaseManager as db
from utils.others import Others

from discord_slash.utils.manage_components import create_select_option

categories = ["Crypto", "Web", "Pwn", "Rev", "Misc"]
challenges = [Others.Challenge(
    i, f"chall{i}", f"author{i}", categories[i % len(categories)], i % 3 == 0) for i in range(27)]

# challenges = [Others.Challenge(*list(challenge))
#               for challenge in db.get_all_challenges()]

print(list(set([challenge.category for challenge in challenges])))

# options = [create_select_option(
#     label=textwrap.shorten(challenge.title, 25, placeholder='...'), value=f"{challenge.id_}") for challenge in challenges]

# options = [(f"{challenge}", f"{challenge.id_}") for challenge in challenges]

# print(options)

# db.refresh_database(new_challenges)

API_KEY = dotenv_values("../.env")['API_KEY']

params = {'API_KEY': API_KEY}

r = requests.get(
    'https://imaginaryctf.org/api/challenges/released', params=params)

challenges = r.json()
all_challenges = []
for challenge in challenges:
    ignore = challenge['author'] == 'Board'
    all_challenges.append(Others.Challenge(
        challenge["id"], challenge["author"], challenge["title"], challenge["category"].split(",")[0], ignore))

db.refresh_database(all_challenges)
