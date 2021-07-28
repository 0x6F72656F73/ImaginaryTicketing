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
    title VARCHAR(255),
    author VARCHAR(255),
    category VARCHAR(255),
    -- helper_id VARCHAR(255), -- will add SOON :tm:
    ignore BOOLEAN
)

-- CREATE TABLE admin (
--   guild_id bigint,
--   message1 VARCHAR(255),
--   message2 VARCHAR(255),
--   message3 VARCHAR(255)
-- );