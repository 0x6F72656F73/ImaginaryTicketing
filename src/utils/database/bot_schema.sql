CREATE TABLE tickets (
    guild_id bigint,
    ticket_id bigint UNIQUE
);

CREATE TABLE requests (
  channel_id bigint,
  channel_name VARCHAR(255),
  guild_id bigint,
  user_id VARCHAR(255),
  ticket_type varchar(255),
  status VARCHAR(255),
  checked BOOLEAN
);

-- CREATE TABLE requests (\n  channel_id bigint,\n  channel_name VARCHAR(255),\n  guild_id bigint,\n  user_id VARCHAR(255),\n  user_name VARCHAR(255),\n  type varchar(255),\n  status VARCHAR(255)\n)
CREATE TABLE archive (
  channel_id bigint,
  channel_name VARCHAR(255),
  guild_id bigint,
  user_id VARCHAR(255),
  ticket_type varchar(255),
  status VARCHAR(255),
  checked BOOLEAN
);

CREATE TABLE challenges (
    id INTEGER UNIQUE,
    author VARCHAR(255),
    title VARCHAR(255),
    category VARCHAR(255),
    helper_id VARCHAR(255),
    ignore BOOLEAN
)

-- CREATE TABLE admin (
--   guild_id bigint,
--   message1 VARCHAR(255),
--   message2 VARCHAR(255),
--   message3 VARCHAR(255)
-- );

-- CREATE TABLE submit (
--   challenge_author VARCHAR(255),
--   title VARCHAR(255),
--   category VARCHAR(255),
--   difficulty VARCHAR(255),
--   description VARCHAR(255),
--   player_attachments VARCHAR(255),
--   admin_attachments VARCHAR(255),
--   general_solve VARCHAR(255),
--   hosting_comments VARCHAR(255),
--   flag VARCHAR(255)
-- )