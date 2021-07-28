import requests
from environs import Env
from utils.database.db import DatabaseManager as db
from utils.others import Others

challenges = [Others.Challenge(*list(chall))
              for chall in db.get_all_challenges()]

print(challenges)
db.refresh_database(challenges)

# env = Env()
# env.read_env()

# params = {'apikey': env.str('API_KEY')}

# r = requests.get(
#     'https://imaginaryctf.org/api/challenges/unapproved', params=params)

# challenges = r.json()
# all_challenges = []
# for challenge in challenges:
#     ignore = challenge['author'] == 'Board'
#     all_challenges.append(Others.Challenge(
#         challenge["id"], challenge["author"], challenge["title"], challenge["category"].split(",")[0], ignore))

# db.refresh_database(all_challenges)
