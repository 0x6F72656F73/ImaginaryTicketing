CREATE TABLE requests (
  channel_id bigint,
  channel_name VARCHAR(255),
  guild_id bigint,
  user_id VARCHAR(255),
  t_type varchar(255),
  status VARCHAR(255),
  bg_check BOOLEAN
);

CREATE TABLE archive (
  channel_id bigint,
  channel_name VARCHAR(255),
  guild_id bigint,
  user_id VARCHAR(255),
  t_type varchar(255),
  status VARCHAR(255),
  bg_check BOOLEAN
);

CREATE TABLE challenges (
    id INTEGER UNIQUE,
    title VARCHAR(255),
    author VARCHAR(255),
    category VARCHAR(255),
    ignore BOOLEAN,
    helper_id_list VARCHAR(255)
);

CREATE TABLE helpers (
  discord_id INTEGER UNIQUE,
  is_available BOOLEAN
);


CREATE TABLE online_helpers (
  channel_id bigint,
  message_id bigint
)