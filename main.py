import discord
from discord.ext import commands
import requests
import settings
import os

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- API Configuration ---
BASE_URL = "https://alerts.globaleas.org/api/v1/alerts"

# --- Helper function for API calls ---
async def fetch_alerts(endpoint, params=None):
    """Fetches alerts from a given API endpoint asynchronously."""
    try:
        # `requests` is a blocking library, so we run it in an executor
        # to avoid blocking the bot's event loop.
        loop = bot.loop
        response = await loop.run_in_executor(
            None, 
            lambda: requests.get(f"{BASE_URL}/{endpoint}", params=params)
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error: {e}")
        return None

# --- Embed and View Creation ---

def create_alert_embed(alert, current_page, total_pages):
    """Creates a Discord embed for a single alert."""
    severity = alert.get("severity", "N/A")
    
    # Set color based on severity
    color = discord.Color.default()
    if severity == "WARNING":
        color = discord.Color.red()
    elif severity == "WATCH":
        color = discord.Color.orange()
    elif severity == "TEST":
        color = discord.Color.blue()

    embed = discord.Embed(
        title=f"Alert: {alert.get('type', 'N/A')} ({severity}) [{current_page}/{total_pages}]",
        description=alert.get("translation", "No translation available."),
        color=color
    )

    footer_text = (
        f"FIPS: {', '.join(alert.get('fipsCodes', [])) or 'N/A'} | "
        f"Callsign: {alert.get('callsign', 'N/A').strip()}\n"
        f"Start: {alert.get('startTime', 'N/A')} | End: {alert.get('endTime', 'N/A')}"
    )
    embed.set_footer(text=footer_text)

    return embed

class AlertPaginator(discord.ui.View):
    """A view for paginating through a list of alerts with buttons."""
    def __init__(self, alerts):
        super().__init__(timeout=180) # View times out after 3 minutes
        self.alerts = alerts
        self.current_page = 0
        self.total_pages = len(alerts)
        self.audio_message = None

    async def update_message(self, interaction: discord.Interaction):
        """Updates the message with the new embed."""
        # Delete previous audio message if it exists
        if self.audio_message:
            try:
                await self.audio_message.delete()
            except discord.NotFound:
                pass
            self.audio_message = None

        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page >= self.total_pages - 1
        
        embed = create_alert_embed(self.alerts[self.current_page], self.current_page + 1, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.grey, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)

    @discord.ui.button(label="EAS Audio", style=discord.ButtonStyle.green, row=1)
    async def audio_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        alert = self.alerts[self.current_page]
        audio_url = alert.get("audioUrl")

        if not audio_url:
            await interaction.response.send_message("No audio available for this alert.", ephemeral=True)
            return

        # Clean up existing audio message if present
        if self.audio_message:
            try:
                await self.audio_message.delete()
            except discord.NotFound:
                pass
            self.audio_message = None

        await interaction.response.defer()
        
        filename = f"eas_audio_{alert.get('id', 'temp')}.mp3"
        
        try:
            loop = interaction.client.loop
            response = await loop.run_in_executor(None, lambda: requests.get(audio_url))
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                file = discord.File(filename)
                self.audio_message = await interaction.followup.send(file=file)
            else:
                await interaction.followup.send("Failed to download audio.", ephemeral=True)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

# --- Generic Command Handler ---
async def handle_alert_command(ctx, alerts):
    """Generic handler for sending paginated alerts."""
    if not alerts:
        await ctx.send("No alerts found.")
        return

    paginator = AlertPaginator(alerts)
    if len(alerts) <= 1:
        paginator.children[1].disabled = True

    initial_embed = create_alert_embed(alerts[0], 1, len(alerts))
    await ctx.send(embed=initial_embed, view=paginator)

# --- Bot Commands ---
@bot.command(name="active")
async def active_alerts(ctx):
    """Displays active CAR alerts."""
    async with ctx.typing():
        alerts = await fetch_alerts("active")
        await handle_alert_command(ctx, alerts)

@bot.command(name="all")
async def all_alerts(ctx):
    """Displays all recent CAR alerts."""
    async with ctx.typing():
        alerts = await fetch_alerts("all")
        await handle_alert_command(ctx, alerts)

@bot.command(name="search")
async def search_alerts_cmd(ctx, *, query: str):
    """Searches for CAR alerts with a given query."""
    async with ctx.typing():
        params = {"query": query, "page": 0}
        alerts = await fetch_alerts("search", params=params)
        await handle_alert_command(ctx, alerts)

# --- Run Bot ---
if __name__ == "__main__":
    if not settings.DISCORD_TOKEN or settings.DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: DISCORD_TOKEN not found or not set in .env file.")
    else:
        bot.run(settings.DISCORD_TOKEN)