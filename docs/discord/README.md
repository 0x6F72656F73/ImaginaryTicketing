# Configuration

**note:** Complete [backend setup][1] first

### Requirements:
- [A discord bot][2]
- Administrator permission

### Backend Setup
1. Edit [src/config.py][3]
   - Change the `OWNERS` to a list of owners. 
     - The only difference between the owners and admins is the owners can shutdown the bot.
   - set `ADMIN_ROLE` and `TICKET_PING_ROLE`
     - the admin role has control over the bot in a guild
     - the role that gets pinged for help and misc tickets
   - set `LOG_CHANNEL_CATEGORY` and `LOG_CHANNEL_NAME`
     - the category and channel name that logs go to
   - set `EMOJIS_MESSAGE`
     - A list of three emojis for reacting to a ticket message
     - If you want animated emoji's, put the emoji in the format `<:emoji_name:emoji_id>`. 
   - set `EMOJIS`
     - A list of three emojis for checking a ticket's type
   - for online transcripts:
     - set `TRANSCRIPT_DOMAIN` and `TRANSCRIPT_PORT`
       - the domain and port the flask server will be hosted on

Once the bot is in the server:

### Discord Setup
2. Create the following roles:
   - $ADMIN_ROLE
     - the admin role
     - does not need any special permissions
   - $TICKET_PING_ROLE
     - the ticket ping role
     - does not need any special permissions
   - Imaginary Tickets (note the name doesn't change anything)
     - the bot's role
     - needs admin perms
3. Give admins the admin role, people willing to answer questions the ticket ping role, and the bot the Bot role.
4. Create the following categories/channels:
   - $LOG_CHANNEL_CATEGORY
     - $LOG_CHANNEL_NAME

At this point, you can start the bot.

5. Verify the bot is all ready:
   - Type `<prefix>check`
   - Verify the output says everything is good. If not, make sure you followed all of the previous steps. 
7. Go to a designated channel people will react to open a ticket, and type `<prefix>ticket`
8. Make sure [developer mode][4] is enabled on your account, right click the embed, copy the message id, and type `<prefix>stm $message_id`
9. Try reacting to the embed 🚀

Running `<prefix>help` and looking at the code for the commands should be more than enough to get you started, and if you have any doubts feel free to dm me or create an issue.

[1]: ../backend/
[2]: https://discord.com/developers/applications
[3]: ../../src/config.py
[4]: https://techswift.org/2020/09/17/how-to-enable-developer-mode-in-discord/
