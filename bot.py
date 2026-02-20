import discord
from discord.ext import commands
import config

# Define the bot's intents
intents = discord.Intents.default()
intents.message_content = True  # Allow the bot to read message content

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Event that fires when the bot is online and ready."""
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

if __name__ == "__main__":
    bot.run(config.DISCORD_TOKEN)