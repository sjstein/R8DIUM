import discord
import msgHandler
from r8udbBotInclude import TOKEN, BOT_CMD, CH_USER


async def send_message(message, user_message, is_private, user_sheet):
    try:
        roles = message.author.roles
        user = message.author.name
        user_id = message.author.id
        channel = str(message.channel)

        response = msgHandler.get_response(user_message, user, user_id, roles, channel, user_sheet)
        if not response:
            return
        await message.author.send(response) if is_private else await message.channel.send(response)

    except Exception as e:
        print(e)


def run_discord_bot(user_sheet):
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} is now running')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        username = str(message.author)
        userid = str(message.author.id)
        user_message = str(message.content)
        channel = str(message.channel)
        if user_message[0:len(BOT_CMD)] == BOT_CMD:
            print(f'{username} ({userid}) wrote: {user_message} on channel: {channel}')
            user_message = user_message[len(BOT_CMD):]
            if channel == CH_USER:
                await send_message(message, user_message, True, user_sheet)
            else:
                await send_message(message, user_message, False, user_sheet)

    client.run(TOKEN)
