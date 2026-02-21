import discord
from discord.ext import commands, tasks
import requests
import settings
import os
import atexit

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# --- API Configuration ---
BASE_URL = "https://alerts.globaleas.org/api/v1/alerts"
HEADERS = {"User-Agent": "emerbot-vortexnet-python"}

# --- EAS Type Mapping ---
EAS_TYPES = {
    "ADR": "Administrative Message",
    "AVA": "Avalanche Watch",
    "AVW": "Avalanche Warning",
    "BLU": "Blue Alert",
    "BZW": "Blizzard Warning",
    "CAE": "Child Abduction Emergency",
    "CDW": "Civil Danger Warning",
    "CEM": "Civil Emergency Message",
    "CFA": "Coastal Flood Watch",
    "CFW": "Coastal Flood Warning",
    "DMO": "Practice/Demo Warning",
    "DSW": "Dust Storm Warning",
    "EAN": "Emergency Action Notification",
    "EAT": "Emergency Action Termination",
    "EQW": "Earthquake Warning",
    "EVI": "Evacuation Immediate",
    "FFA": "Flash Flood Watch",
    "FFW": "Flash Flood Warning",
    "FLA": "Flood Watch",
    "FLW": "Flood Warning",
    "FRW": "Fire Warning",
    "FSW": "Flash Freeze Warning",
    "FZW": "Freeze Warning",
    "HLS": "Hurricane Local Statement",
    "HMW": "Hazardous Materials Warning",
    "HUA": "Hurricane Watch",
    "HUW": "Hurricane Warning",
    "HWA": "High Wind Watch",
    "HWW": "High Wind Warning",
    "LAE": "Local Area Emergency",
    "LEW": "Law Enforcement Warning",
    "NAT": "National Audible Test",
    "NIC": "National Information Center",
    "NPT": "National Periodic Test",
    "NUW": "Nuclear Power Plant Warning",
    "RHW": "Radiological Hazard Warning",
    "RMT": "Required Monthly Test",
    "RWT": "Required Weekly Test",
    "SMW": "Special Marine Warning",
    "SPS": "Special Weather Statement",
    "SPW": "Shelter In Place Warning",
    "SVA": "Severe Thunderstorm Watch",
    "SVR": "Severe Thunderstorm Warning",
    "TOA": "Tornado Watch",
    "TOE": "911 Telephone Outage Emergency",
    "TOR": "Tornado Warning",
    "TRA": "Tropical Storm Watch",
    "TRW": "Tropical Storm Warning",
    "TSA": "Tsunami Watch",
    "TSW": "Tsunami Warning",
    "VOW": "Volcano Warning",
    "WSA": "Winter Storm Watch",
    "WSW": "Winter Storm Warning"
}

# --- Helper function for API calls ---
async def fetch_alerts(endpoint, params=None):
    """Fetches alerts from a given API endpoint asynchronously."""
    try:
        # `requests` is a blocking library, so we run it in an executor
        # to avoid blocking the bot's event loop.
        loop = bot.loop
        response = await loop.run_in_executor(
            None, 
            lambda: requests.get(f"{BASE_URL}/{endpoint}", params=params, headers=HEADERS)
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
    color = discord.Color(0xffffff)

    alert_type_code = alert.get('type', 'N/A')
    if alert_type_code in EAS_TYPES:
        alert_display = f"{alert_type_code} ({EAS_TYPES[alert_type_code]})"
    else:
        alert_display = alert_type_code

    embed = discord.Embed(
        title=f"Alert: {alert_display} ({severity}) [{current_page}/{total_pages}]",
        description=alert.get("translation", "No translation available."),
        color=color
    )
    embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")

    footer_text = (
        f"FIPS: {', '.join(alert.get('fipsCodes') or []) or 'N/A'} | "
        f"Issued by/Callsign: {(alert.get('callsign') or 'N/A').strip()}\n"
        f"Start: {alert.get('startTime', 'N/A')} | End: {alert.get('endTime', 'N/A')}"
    )
    embed.set_footer(text=footer_text)

    return embed

class AlertPaginator(discord.ui.View):
    """A view for paginating through a list of alerts with buttons."""
    def __init__(self, alerts, author):
        super().__init__(timeout=180) # View times out after 3 minutes
        self.alerts = alerts
        self.author = author
        self.current_page = 0
        self.total_pages = len(alerts)
        self.audio_message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this pagination view.", ephemeral=True)
            return False
        return True

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
        # Previous is at index 0, Next is at index 2
        self.children[2].disabled = self.current_page >= self.total_pages - 1
        
        embed = create_alert_embed(self.alerts[self.current_page], self.current_page + 1, self.total_pages)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.grey, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="EAS Audio", style=discord.ButtonStyle.green)
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

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)

# --- Generic Command Handler ---
async def handle_alert_command(ctx, alerts):
    """Generic handler for sending paginated alerts."""
    if not alerts:
        await ctx.send("No alerts found.")
        return

    paginator = AlertPaginator(alerts, ctx.author)
    if len(alerts) <= 1:
        # Next button is at index 2
        paginator.children[2].disabled = True

    initial_embed = create_alert_embed(alerts[0], 1, len(alerts))
    await ctx.send(embed=initial_embed, view=paginator)

# --- Background Tasks ---
SENT_ALERTS_FILE = "sent_alerts.txt"

def cleanup_sent_alerts():
    if os.path.exists(SENT_ALERTS_FILE):
        try:
            os.remove(SENT_ALERTS_FILE)
        except OSError:
            pass

atexit.register(cleanup_sent_alerts)

# Load existing alerts if file exists (e.g. from crash)
sent_alert_ids = set()
if os.path.exists(SENT_ALERTS_FILE):
    with open(SENT_ALERTS_FILE, "r") as f:
        sent_alert_ids = set(line.strip() for line in f if line.strip())

@tasks.loop(minutes=3)
async def check_alerts():
    """Checks for active alerts every 3 minutes and posts new ones."""
    if not settings.CHANNEL_ID or not str(settings.CHANNEL_ID).isdigit():
        print("Error: CHANNEL_ID is missing or invalid in .env")
        return

    channel = bot.get_channel(int(settings.CHANNEL_ID))
    if not channel:
        print(f"Warning: Channel with ID {settings.CHANNEL_ID} not found.")
        return

    print("Fetching active alerts...")
    alerts = await fetch_alerts("active")

    if alerts is not None:
        count = len(alerts)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{count} active alerts"))

    if not alerts:
        print("No active alerts found.")
        return

    for alert in alerts:
        alert_id = str(alert.get("id"))
        if alert_id not in sent_alert_ids:
            print(f"New alert detected: {alert_id}. Sending...")
            embed = create_alert_embed(alert, 1, 1)
            
            content = ""
            if settings.ROLE_ID and str(settings.ROLE_ID).strip().isdigit():
                content = f"<@&{settings.ROLE_ID.strip()}>"

            # Handle Audio
            audio_url = alert.get("audioUrl")
            file = None
            temp_filename = f"temp_audio_{alert_id}.mp3"
            
            if audio_url:
                try:
                    loop = bot.loop
                    response = await loop.run_in_executor(None, lambda: requests.get(audio_url))
                    if response.status_code == 200:
                        with open(temp_filename, 'wb') as f:
                            f.write(response.content)
                        file = discord.File(temp_filename)
                except Exception as e:
                    print(f"Failed to download audio for alert {alert_id}: {e}")

            try:
                await channel.send(content=content, embed=embed, file=file)
                
                sent_alert_ids.add(alert_id)
                with open(SENT_ALERTS_FILE, "a") as f:
                    f.write(f"{alert_id}\n")
                print(f"Alert {alert_id} sent successfully.")
            except Exception as e:
                print(f"Failed to send alert {alert_id}: {e}")
            finally:
                if file:
                    file.close()
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)

# --- Bot Commands ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    
    if settings.ROLE_ID and str(settings.ROLE_ID).strip().isdigit():
        print(f"Role Ping Enabled: {settings.ROLE_ID}")
    else:
        print("Role Ping Disabled: ROLE_ID is missing or invalid.")

    if not check_alerts.is_running():
        check_alerts.start()
    print('------')

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

@bot.command(name="help")
async def help_command(ctx):
    """Displays the help menu."""
    embed = discord.Embed(
        title="Emer Bot Help",
        description="List of available commands:",
        color=discord.Color(0xffffff)
    )
    embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")
    
    embed.add_field(name="!active", value="Displays currently active CAR alerts.", inline=False)
    embed.add_field(name="!all", value="Displays all recent CAR alerts.", inline=False)
    embed.add_field(name="!search <query>", value="Searches for alerts matching the query.", inline=False)
    embed.add_field(name="!help", value="Displays this help message.", inline=False)
    
    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    await ctx.send(embed=embed)

# --- Run Bot ---
if __name__ == "__main__":
    if not settings.DISCORD_TOKEN or settings.DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: DISCORD_TOKEN not found or not set in .env file.")
    else:
        bot.run(settings.DISCORD_TOKEN)