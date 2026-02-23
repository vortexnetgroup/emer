import discord
from discord.ext import commands, tasks
import requests
import settings
import os
import atexit
import datetime
import av
import random
import asyncio
import json
import re
import html
import sys
import subprocess

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True

class EmerBot(commands.Bot):
    async def setup_hook(self):
        await self.tree.sync()

bot = EmerBot(command_prefix="!", intents=intents, help_command=None)

# Store active radio controller messages: {guild_id: message}
active_radio_controllers = {}

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

# --- EAS Rarity Mapping ---
EAS_RARITY = {
    "ADR": "Common",
    "AVA": "Uncommon",
    "AVW": "Uncommon",
    "BLU": "Rare",
    "BZW": "Uncommon",
    "CAE": "Rare",
    "CDW": "Extremely Rare",
    "CEM": "Rare",
    "CFA": "Common",
    "CFW": "Common",
    "DMO": "Common",
    "DSW": "Uncommon",
    "EAN": "Extremely Rare",
    "EAT": "Extremely Rare",
    "EQW": "Extremely Rare",
    "EVI": "Rare",
    "FFA": "Common",
    "FFW": "Common",
    "FLA": "Common",
    "FLW": "Common",
    "FRW": "Rare",
    "FSW": "Uncommon",
    "FZW": "Common",
    "HLS": "Common",
    "HMW": "Rare",
    "HUA": "Uncommon",
    "HUW": "Uncommon",
    "HWA": "Common",
    "HWW": "Common",
    "LAE": "Rare",
    "LEW": "Rare",
    "NAT": "Extremely Rare",
    "NIC": "Extremely Rare",
    "NPT": "Uncommon",
    "NUW": "Extremely Rare",
    "RHW": "Extremely Rare",
    "RMT": "Common",
    "RWT": "Common",
    "SMW": "Common",
    "SPS": "Common",
    "SPW": "Rare",
    "SVA": "Common",
    "SVR": "Common",
    "TOA": "Common",
    "TOE": "Rare",
    "TOR": "Uncommon",
    "TRA": "Uncommon",
    "TRW": "Uncommon",
    "TSA": "Rare",
    "TSW": "Rare",
    "VOW": "Extremely Rare",
    "WSA": "Common",
    "WSW": "Common"
}

# --- IEMBot Rooms ---
IEMBOT_ROOMS = {
    "botstalk": "All Bots Talk",
    "nhcchat": "National Hurricane Center (NHC)",
    "spcchat": "Storm Prediction Center (SPC)",
    "cpcchat": "Climate Prediction Center (CPC)",
    "wpcchat": "Weather Prediction Center (WPC)",
    "wbcchat": "Weather Bureau Central / NWSHQ (WBC)",
    "dmgchat": "Damage Assessment PNS",
    "pdschat": "Particularly Dangerous Situation PDS",
    "emergchat": "Tornado/FF Emergencies",
    "abqchat": "Albuquerque",
    "abrchat": "Aberdeen",
    "afcchat": "Anchorage",
    "afgchat": "Fairbanks",
    "ajkchat": "Juneau",
    "akqchat": "Wakefield",
    "alychat": "Albany",
    "amachat": "Amarillo",
    "apxchat": "Gaylord",
    "arxchat": "La Crosse",
    "bgmchat": "Binghamton",
    "bischat": "Bismarck",
    "bmxchat": "Birmingham",
    "boichat": "Boise",
    "bouchat": "Denver",
    "boxchat": "Boston/Taunton",
    "brochat": "Brownsville",
    "btvchat": "Burlington",
    "bufchat": "Buffalo",
    "byzchat": "Billings",
    "caechat": "Columbia",
    "carchat": "Caribou",
    "chschat": "Charleston",
    "clechat": "Cleveland",
    "crpchat": "Corpus Christi",
    "ctpchat": "State College",
    "cyschat": "Cheyenne",
    "ddcchat": "Dodge City",
    "dlhchat": "Duluth",
    "dmxchat": "Des Moines",
    "dtxchat": "Detroit",
    "dvnchat": "Quad Cities Ia",
    "eaxchat": "Kansas City/Pleasant Hill",
    "ekachat": "Eureka",
    "epzchat": "El Paso Tx/Santa Teresa",
    "ewxchat": "Austin/San Antonio",
    "ffcchat": "Peachtree City",
    "fgfchat": "Grand Forks",
    "fgzchat": "Flagstaff",
    "fsdchat": "Sioux Falls",
    "fwdchat": "Dallas/Fort Worth",
    "ggwchat": "Glasgow",
    "gidchat": "Hastings",
    "gjtchat": "Grand Junction",
    "gldchat": "Goodland",
    "grbchat": "Green Bay",
    "grrchat": "Grand Rapids",
    "gspchat": "Greenville/Spartanburg",
    "gumchat": "Guam",
    "gyxchat": "Gray",
    "hawaii": "Hawaii",
    "hfochat": "Honolulu",
    "hgxchat": "Houston/Galveston",
    "hnxchat": "San Joaquin Valley/Hanford",
    "hunchat": "Huntsville",
    "ictchat": "Wichita",
    "ilmchat": "Wilmington",
    "ilnchat": "Wilmington",
    "ilxchat": "Lincoln",
    "indchat": "Indianapolis",
    "iwxchat": "Northern Indiana",
    "janchat": "Jackson",
    "jaxchat": "Jacksonville",
    "jklchat": "Jackson",
    "jsjchat": "San Juan",
    "keychat": "Key West",
    "lbfchat": "North Platte",
    "lchchat": "Lake Charles",
    "lixchat": "New Orleans",
    "lknchat": "Elko",
    "lmkchat": "Louisville",
    "lotchat": "Chicago",
    "loxchat": "Los Angeles/Oxnard",
    "lsxchat": "St Louis",
    "lubchat": "Lubbock",
    "lwxchat": "Baltimore Md/ Washington Dc",
    "lzkchat": "Little Rock",
    "mafchat": "Midland/Odessa",
    "megchat": "Memphis",
    "mflchat": "Miami",
    "mfrchat": "Medford",
    "mhxchat": "Newport/Morehead City",
    "michiganwxalerts": "Michigan Weather Alerts",
    "mkxchat": "Milwaukee/Sullivan",
    "mlbchat": "Melbourne",
    "mobchat": "Mobile",
    "mpxchat": "Twin Cities/Chanhassen",
    "mqtchat": "Marquette",
    "mrxchat": "Morristown",
    "msochat": "Missoula",
    "mtrchat": "San Francisco",
    "oaxchat": "Omaha/Valley",
    "ohxchat": "Nashville",
    "okxchat": "New York",
    "otxchat": "Spokane",
    "ounchat": "Norman",
    "pahchat": "Paducah",
    "pbzchat": "Pittsburgh",
    "pdtchat": "Pendleton",
    "phichat": "Mount Holly",
    "pihchat": "Pocatello/Idaho Falls",
    "pqrchat": "Portland",
    "psrchat": "Phoenix",
    "pubchat": "Pueblo",
    "rahchat": "Raleigh",
    "revchat": "Reno",
    "riwchat": "Riverton",
    "rlxchat": "Charleston",
    "rnkchat": "Blacksburg",
    "sewchat": "Seattle",
    "sgfchat": "Springfield",
    "sgxchat": "San Diego",
    "shvchat": "Shreveport",
    "sjtchat": "San Angelo",
    "sjuchat": "San Juan",
    "slcchat": "Salt Lake City",
    "stochat": "Sacramento",
    "taechat": "Tallahassee",
    "tbwchat": "Tampa Bay Area/Ruskin",
    "tfxchat": "Great Falls",
    "topchat": "Topeka",
    "tsachat": "Tulsa",
    "twcchat": "Tucson",
    "unrchat": "Rapid City",
    "vefchat": "Las Vegas",
    "alrchat": "Atlanta RFC",
    "fwrchat": "West Gulf RFC",
    "krfchat": "Missouri River Basin RFC",
    "msrchat": "North Central RFC",
    "ornchat": "Lower Mississippi RFC",
    "pacrchat": "Alaska - Pacific RFC",
    "ptrchat": "Northwest RFC",
    "rhachat": "Mid Atlantic RFC",
    "rsachat": "California - Nevada RFC",
    "strchat": "Colorado RFC",
    "tarchat": "Northeast RFC",
    "tirchat": "Ohio RFC",
    "tuachat": "Arkansas Red River RFC",
    "pancchat": "Anchorage",
    "zabchat": "Albuquerque",
    "zauchat": "Chicago",
    "zbwchat": "Boston",
    "zdcchat": "Washington DC",
    "zdvchat": "Denver",
    "zfwchat": "Fort Worth",
    "zhnchat": "Honolulu CWSU",
    "zhuchat": "Houston",
    "zidchat": "Indianapolis",
    "zjxchat": "Jacksonville",
    "zkcchat": "Kansas City",
    "zlachat": "Los Angeles",
    "zlcchat": "Salt Lake City",
    "zmachat": "Miami",
    "zmechat": "Memphis",
    "zmpchat": "Minneapolis",
    "znychat": "New York",
    "zoachat": "Oakland",
    "zobchat": "Cleveland",
    "zsechat": "Seattle",
    "ztlchat": "Atlanta",
    "n90": "N90 TRACON New York City",
    "potomac_tracon": "Potomac TRACON Washington DC",
    "phl": "PHL TRACON Philadephia"
}

# --- US States Mapping ---
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida", "GA": "Georgia",
    "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
    "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York", "NC": "North Carolina",
    "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
    "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming",
    # Territories
    "AS": "American Samoa", "DC": "District of Columbia", "FM": "Federated States of Micronesia",
    "GU": "Guam", "MH": "Marshall Islands", "MP": "Northern Mariana Islands", "PW": "Palau",
    "PR": "Puerto Rico", "VI": "U.S. Virgin Islands"
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

async def fetch_iembot_messages(room):
    """Fetches messages from IEMBot for a specific room."""
    url = f"https://weather.im/iembot-json/room/{room}?seqnum=0"
    try:
        loop = bot.loop
        response = await loop.run_in_executor(None, lambda: requests.get(url))
        response.raise_for_status()
        
        content = response.text
        # Extract JSON if wrapped in HTML/XML (find first { and last })
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            content = content[start:end]
            
        data = json.loads(content)
        return data.get("messages", [])
    except Exception as e:
        print(f"IEMBot API Error: {e}")
        return None

# --- Embed and View Creation ---

def format_time_to_discord(time_str):
    """Converts an ISO 8601 time string to a Discord timestamp format."""
    if not time_str or time_str == "N/A":
        return "N/A"
    try:
        # Handle 'Z' for UTC which fromisoformat might not like on all python versions
        if time_str.endswith('Z'):
            dt_obj = datetime.datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        else:
            dt_obj = datetime.datetime.fromisoformat(time_str)

        # If the datetime object is naive (no timezone), assume it's UTC.
        if dt_obj.tzinfo is None:
            dt_obj = dt_obj.replace(tzinfo=datetime.timezone.utc)
            
        timestamp = int(dt_obj.timestamp())
        return f"<t:{timestamp}:f>"
    except (ValueError, TypeError):
        # Fallback to original string if parsing fails
        return time_str

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

    rarity = EAS_RARITY.get(alert_type_code, "Unknown")

    embed = discord.Embed(
        title=f"Alert: {alert_display} ({severity}) [{current_page}/{total_pages}]",
        description=alert.get("translation", "No translation available."),
        color=color
    )
    embed.add_field(name="Rarity", value=rarity, inline=True)
    embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")

    start_time = format_time_to_discord(alert.get('startTime', 'N/A'))
    end_time = format_time_to_discord(alert.get('endTime', 'N/A'))

    embed.add_field(name="Start Time", value=start_time, inline=True)
    embed.add_field(name="End Time", value=end_time, inline=True)

    footer_text = (
        f"FIPS: {', '.join(alert.get('fipsCodes') or []) or 'N/A'} | "
        f"Issued by/Callsign: {(alert.get('callsign') or 'N/A').strip()}"
    )
    embed.set_footer(text=footer_text)

    return embed

def clean_iembot_message(text):
    """Cleans HTML tags from IEMBot messages and formats for Discord."""
    if not text:
        return "No content"
    
    # Decode HTML entities
    text = html.unescape(text)
    
    # Replace <br> with newlines
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    
    # Replace </p> with newlines to separate paragraphs
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)
    
    # Replace links: <a href="url">text</a> -> [text](url)
    text = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)
    text = re.sub(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.IGNORECASE)
    
    # Replace bold: <strong>text</strong> -> **text**
    text = re.sub(r'<(?:strong|b)>(.*?)</(?:strong|b)>', r'**\1**', text, flags=re.IGNORECASE)
    
    # Remove remaining tags (like <p>)
    text = re.sub(r'<[^>]+>', '', text)
    
    return text.strip()

def create_iembot_embed(message, current_page, total_pages, room_code):
    """Creates a Discord embed for an IEMBot message."""
    room_name = IEMBOT_ROOMS.get(room_code, room_code)
    clean_desc = clean_iembot_message(message.get("message", "No content"))
    
    embed = discord.Embed(
        title=f"IEMBot: {room_name} [{current_page}/{total_pages}]",
        description=clean_desc,
        color=discord.Color(0xffffff)
    )
    embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")
    
    footer_text = f"Time: {message.get('ts', 'N/A')} | Author: {message.get('author', 'N/A')}\nProduct ID: {message.get('product_id', 'N/A')}"
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
        
        filename = settings.BASE_DIR / f"eas_audio_{alert.get('id', 'temp')}.mp3"
        
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

class IEMBotPaginator(discord.ui.View):
    """A view for paginating through IEMBot messages."""
    def __init__(self, messages, author, room_code):
        super().__init__(timeout=180)
        self.messages = messages
        self.author = author
        self.room_code = room_code
        self.current_page = 0
        self.total_pages = len(messages)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You cannot control this pagination view.", ephemeral=True)
            return False
        return True

    async def update_message(self, interaction: discord.Interaction):
        self.children[0].disabled = self.current_page == 0
        self.children[1].disabled = self.current_page >= self.total_pages - 1
        
        embed = create_iembot_embed(self.messages[self.current_page], self.current_page + 1, self.total_pages, self.room_code)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.grey, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.grey)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update_message(interaction)

# --- Generic Command Handler ---
async def handle_alert_command(interaction: discord.Interaction, alerts):
    """Generic handler for sending paginated alerts."""
    if not alerts:
        await interaction.followup.send("No alerts found.")
        return

    paginator = AlertPaginator(alerts, interaction.user)
    if len(alerts) <= 1:
        # Next button is at index 2
        paginator.children[2].disabled = True

    initial_embed = create_alert_embed(alerts[0], 1, len(alerts))
    await interaction.followup.send(embed=initial_embed, view=paginator)

# --- Radio Functionality ---
def load_stations():
    stations = {}
    stations_file = settings.BASE_DIR / "stations.txt"
    if os.path.exists(stations_file):
        with open(stations_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                parts = line.strip().rsplit(" ", 1)
                if len(parts) == 2:
                    stations[parts[0].strip()] = parts[1].strip()
    return stations

class PyAVSource(discord.AudioSource):
    def __init__(self, url):
        # Open the stream with reconnection options for stability
        self.source = av.open(url, options={
            'reconnect': '1',
            'reconnect_streamed': '1',
            'reconnect_delay_max': '5'
        })
        self.stream = self.source.streams.audio[0]
        # Discord requires 48KHz, 16-bit stereo PCM
        self.resampler = av.AudioResampler(format='s16', layout='stereo', rate=48000)
        self.packet_iter = self.source.decode(self.stream)
        self.buffer = bytearray()

    def read(self):
        # Discord expects 20ms of audio (3840 bytes for stereo 16-bit 48kHz)
        required_bytes = 3840
        
        while len(self.buffer) < required_bytes:
            try:
                packet = next(self.packet_iter)
                frames = self.resampler.resample(packet)
                for frame in frames:
                    self.buffer.extend(frame.to_ndarray().tobytes())
            except (StopIteration, av.AVError):
                # End of stream or error, return whatever is left
                return bytes(self.buffer)
        
        data = bytes(self.buffer[:required_bytes])
        del self.buffer[:required_bytes]
        return data

    def cleanup(self):
        self.source.close()

class RadioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            
        if interaction.guild.id in active_radio_controllers:
            del active_radio_controllers[interaction.guild.id]

        embed = discord.Embed(description="The media has stopped.", color=discord.Color(0xffffff))
        await interaction.response.edit_message(embed=embed, view=None)
        
        await asyncio.sleep(3)
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

    @discord.ui.button(label="Vol +", style=discord.ButtonStyle.blurple)
    async def vol_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
            new_vol = min(vc.source.volume + 0.1, 2.0)
            vc.source.volume = new_vol
            await interaction.response.send_message(f"Volume increased to {int(new_vol * 100)}%", ephemeral=True)
        else:
            await interaction.response.send_message("Cannot adjust volume (not playing or invalid source).", ephemeral=True)

    @discord.ui.button(label="Vol -", style=discord.ButtonStyle.blurple)
    async def vol_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = interaction.guild.voice_client
        if vc and vc.source and isinstance(vc.source, discord.PCMVolumeTransformer):
            new_vol = max(vc.source.volume - 0.1, 0.0)
            vc.source.volume = new_vol
            await interaction.response.send_message(f"Volume decreased to {int(new_vol * 100)}%", ephemeral=True)
        else:
            await interaction.response.send_message("Cannot adjust volume (not playing or invalid source).", ephemeral=True)

    @discord.ui.button(label="Station List", style=discord.ButtonStyle.grey)
    async def station_list(self, interaction: discord.Interaction, button: discord.ui.Button):
        stations = load_stations()
        if not stations:
            await interaction.response.send_message("No stations found in stations.txt.", ephemeral=True)
            return
        
        desc = "\n".join([f"• {name}" for name in stations.keys()])
        if len(desc) > 4000:
            desc = desc[:4000] + "..."
            
        embed = discord.Embed(title="Available Stations", description=desc, color=discord.Color(0xffffff))
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def station_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    stations = load_stations()
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in stations.keys()
        if current.lower() in name.lower()
    ][:25]

# --- Background Tasks ---
SENT_ALERTS_FILE = settings.BASE_DIR / "sent_alerts.txt"

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

# Get local timezone for scheduling
local_tz = datetime.datetime.now().astimezone().tzinfo

@tasks.loop(time=datetime.time(hour=13, minute=0, tzinfo=local_tz))
async def clear_sent_alerts_task():
    """Clears the sent alerts cache and file at 1 PM machine time."""
    sent_alert_ids.clear()
    if os.path.exists(SENT_ALERTS_FILE):
        open(SENT_ALERTS_FILE, 'w').close()
    print(f"Cleared sent alerts cache and file at {datetime.datetime.now()}.")

@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=local_tz))
async def auto_update_task():
    """Checks for updates automatically at midnight."""
    await bot.loop.run_in_executor(None, check_for_updates)

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
            temp_filename = settings.BASE_DIR / f"temp_audio_{alert_id}.mp3"
            
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
    if not clear_sent_alerts_task.is_running():
        clear_sent_alerts_task.start()
    if not auto_update_task.is_running():
        auto_update_task.start()
    print('------')

@bot.tree.command(name="active", description="Displays active CAR alerts.")
async def active_alerts(interaction: discord.Interaction):
    await interaction.response.defer()
    alerts = await fetch_alerts("active")
    await handle_alert_command(interaction, alerts)

@bot.tree.command(name="all", description="Displays all recent CAR alerts.")
async def all_alerts(interaction: discord.Interaction):
    await interaction.response.defer()
    alerts = await fetch_alerts("all")
    await handle_alert_command(interaction, alerts)

@bot.tree.command(name="search", description="Searches for CAR alerts with a given query.")
async def search_alerts_cmd(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    params = {"query": query, "page": 0}
    alerts = await fetch_alerts("search", params=params)
    await handle_alert_command(interaction, alerts)

async def iembot_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    choices = []
    for code, name in IEMBOT_ROOMS.items():
        if current.lower() in code.lower() or current.lower() in name.lower():
            display_name = f"[{code}] {name}"
            choices.append(discord.app_commands.Choice(name=display_name, value=code))
            if len(choices) >= 25:
                break
    return choices

@bot.tree.command(name="iembot", description="Displays recent messages from an IEMBot chatroom.")
@discord.app_commands.describe(chatroom="The chatroom to fetch messages from")
@discord.app_commands.autocomplete(chatroom=iembot_autocomplete)
async def iembot_command(interaction: discord.Interaction, chatroom: str):
    await interaction.response.defer()
    
    messages = await fetch_iembot_messages(chatroom)
    
    if not messages:
        await interaction.followup.send(f"No messages found for room '{chatroom}' or API error.")
        return

    # Get last 5 and reverse so newest is first
    recent_messages = messages[-5:]
    # Reverse so newest is first
    recent_messages = messages
    recent_messages.reverse()
    
    if not recent_messages:
         await interaction.followup.send(f"No recent messages found for room '{chatroom}'.")
         return

    paginator = IEMBotPaginator(recent_messages, interaction.user, chatroom)
    if len(recent_messages) <= 1:
        paginator.children[1].disabled = True

    initial_embed = create_iembot_embed(recent_messages[0], 1, len(recent_messages), chatroom)
    await interaction.followup.send(embed=initial_embed, view=paginator)

@bot.tree.command(name="help", description="Displays the help menu.")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Emer Bot Help",
        description="List of available commands:",
        color=discord.Color(0xffffff)
    )
    embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")
    
    # Dynamically list commands from the tree
    for command in bot.tree.get_commands():
        embed.add_field(name=f"/{command.name}", value=command.description, inline=False)
    
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    await interaction.response.send_message(embed=embed)

    # One in a million chance for a surprise
    if random.randint(1, 1_000_000) == 1:
        corncat_path = settings.BASE_DIR / "corncat.png"
        if os.path.exists(corncat_path):
            message = "congrats, this is a GWES reference. Dear corncat has came for you. 1 in a million chance for this to happen, lucky you! - dev1"
            await interaction.followup.send(message, file=discord.File(corncat_path))
        else:
            # This will only be visible to the bot owner in the console.
            print("Special help command triggered, but corncat.png is missing.")

@bot.tree.command(name="weather-radio", description="Plays a weather radio station.")
@discord.app_commands.describe(station="The name of the station to play")
@discord.app_commands.autocomplete(station=station_autocomplete)
async def weather_radio(interaction: discord.Interaction, station: str):
    if not interaction.user.voice:
        await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True)
        return

    stations = load_stations()
    url = stations.get(station)
    
    if not url:
        await interaction.response.send_message(f"Station '{station}' not found.", ephemeral=True)
        return

    await interaction.response.defer()

    # Connect to voice
    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client
    
    if vc and vc.is_connected():
        if vc.channel != channel:
            await vc.move_to(channel)
    else:
        vc = await channel.connect()

    # Stop existing playback
    if vc.is_playing():
        vc.stop()

    # Play stream using PyAV
    try:
        source = PyAVSource(url)
        transformer = discord.PCMVolumeTransformer(source, volume=0.5)
        vc.play(transformer)
        
        embed = discord.Embed(
            title="Weather Radio",
            description=f"Now playing: **{station}**\nConnected to: {channel.mention}",
            color=discord.Color(0xffffff)
        )
        embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")
        
        guild_id = interaction.guild.id
        if guild_id in active_radio_controllers:
            try:
                msg = active_radio_controllers[guild_id]
                await msg.edit(embed=embed, view=RadioView())
                await interaction.followup.send(f"Tuned to **{station}**.", ephemeral=True)
                return
            except (discord.NotFound, discord.HTTPException):
                pass

        msg = await interaction.followup.send(embed=embed, view=RadioView())
        active_radio_controllers[guild_id] = msg
    except Exception as e:
        await interaction.followup.send(f"Error playing station: {e}")

# --- Weather Command Helpers ---
async def get_location_from_zip(zipcode):
    url = f"http://api.zippopotam.us/us/{zipcode}"
    try:
        loop = bot.loop
        response = await loop.run_in_executor(None, lambda: requests.get(url))
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        place = data['places'][0]
        return {
            "lat": place['latitude'],
            "lon": place['longitude'],
            "city": place['place name'],
            "state": place['state abbreviation']
        }
    except Exception:
        return None

def get_weather_emoji(condition):
    condition = condition.lower()
    if "sunny" in condition or "clear" in condition: return "☀️"
    if "partly cloudy" in condition: return "⛅"
    if "cloud" in condition: return "☁️"
    if "rain" in condition or "shower" in condition: return "🌧️"
    if "thunder" in condition or "t-storm" in condition: return "⛈️"
    if "snow" in condition or "flurries" in condition: return "❄️"
    if "fog" in condition or "mist" in condition: return "🌫️"
    if "wind" in condition: return "💨"
    return "🌡️"

@bot.tree.command(name="nwsforecast", description="Get the NWS forecast for a ZIP code.")
@discord.app_commands.describe(zipcode="The 5-digit ZIP code")
async def nws_forecast(interaction: discord.Interaction, zipcode: str):
    if not zipcode.isdigit() or len(zipcode) != 5:
        await interaction.response.send_message("Please enter a valid 5-digit ZIP code.", ephemeral=True)
        return

    await interaction.response.defer()

    # 1. Get Location Data
    loc_data = await get_location_from_zip(zipcode)
    if not loc_data:
        await interaction.followup.send(f"Could not find location for ZIP code: {zipcode}")
        return

    lat, lon = loc_data['lat'], loc_data['lon']
    city, state = loc_data['city'], loc_data['state']

    # 2. Get NWS Grid Data
    try:
        loop = bot.loop
        points_url = f"https://api.weather.gov/points/{lat},{lon}"
        points_resp = await loop.run_in_executor(None, lambda: requests.get(points_url, headers=HEADERS))
        points_resp.raise_for_status()
        points_data = points_resp.json()
        
        props = points_data['properties']
        forecast_url = props['forecast']
        stations_url = props['observationStations']
        
        # 3. Fetch Forecast, Alerts, and Observations
        # Forecast
        forecast_resp = await loop.run_in_executor(None, lambda: requests.get(forecast_url, headers=HEADERS))
        forecast_data = forecast_resp.json() if forecast_resp.status_code == 200 else None

        # Alerts
        alerts_url = f"https://api.weather.gov/alerts/active?point={lat},{lon}"
        alerts_resp = await loop.run_in_executor(None, lambda: requests.get(alerts_url, headers=HEADERS))
        alerts_data = alerts_resp.json() if alerts_resp.status_code == 200 else None

        # Observations
        obs_data = None
        stations_resp = await loop.run_in_executor(None, lambda: requests.get(stations_url, headers=HEADERS))
        if stations_resp.status_code == 200:
            stations_list = stations_resp.json().get('features', [])
            if stations_list:
                station_id = stations_list[0]['id']
                obs_url = f"{station_id}/observations/latest"
                obs_resp = await loop.run_in_executor(None, lambda: requests.get(obs_url, headers=HEADERS))
                if obs_resp.status_code == 200:
                    obs_data = obs_resp.json()

    except Exception as e:
        await interaction.followup.send(f"Error fetching weather data: {e}")
        return

    # 4. Build Embed
    embed = discord.Embed(title=f"Weather for {city}, {state} ({zipcode})", color=discord.Color(0xffffff))
    embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")

    # Current Conditions
    if obs_data:
        props = obs_data.get('properties', {})
        temp_c = props.get('temperature', {}).get('value')
        temp_f = (temp_c * 9/5) + 32 if temp_c is not None else None
        weather_desc = props.get('textDescription', 'Unknown')
        humidity = props.get('relativeHumidity', {}).get('value')
        wind_speed = props.get('windSpeed', {}).get('value')
        wind_mph = (wind_speed * 0.621371) if wind_speed is not None else 0
        
        emoji = get_weather_emoji(weather_desc)
        
        obs_str = f"{emoji} **{weather_desc}**\n"
        if temp_f is not None:
            obs_str += f"🌡️ **Temp:** {int(temp_f)}°F ({int(temp_c)}°C)\n"
        if humidity is not None:
            obs_str += f"💧 **Humidity:** {int(humidity)}%\n"
        if wind_mph is not None:
            obs_str += f"💨 **Wind:** {int(wind_mph)} mph"
            
        embed.add_field(name="Current Conditions", value=obs_str, inline=False)

    # Alerts
    if alerts_data and alerts_data.get('features'):
        alert_lines = []
        for feature in alerts_data['features'][:5]: # Limit to 5
            props = feature['properties']
            event = props['event']
            severity = props['severity']
            emoji = "⚠️" if severity in ["Severe", "Extreme"] else "📢"
            alert_lines.append(f"{emoji} **{event}**")
        
        if alert_lines:
            embed.add_field(name="🚨 Active Alerts", value="\n".join(alert_lines), inline=False)
    else:
        embed.add_field(name="🚨 Active Alerts", value="No active alerts.", inline=False)

    # Forecast
    if forecast_data:
        periods = forecast_data['properties']['periods'][:3] # Next 3 periods
        for period in periods:
            name = period['name']
            temp = period['temperature']
            unit = period['temperatureUnit']
            desc = period['shortForecast']
            emoji = get_weather_emoji(desc)
            embed.add_field(name=f"{name}", value=f"{emoji} {desc}, {temp}°{unit}", inline=True)

    embed.set_footer(text="Data provided by National Weather Service")
    await interaction.followup.send(embed=embed)

async def state_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    return [
        discord.app_commands.Choice(name=f"{name} ({abbr})", value=abbr)
        for abbr, name in US_STATES.items()
        if current.lower() in name.lower() or current.lower() in abbr.lower()
    ][:25]

@bot.tree.command(name="iemradmap", description="Generates a radar map from IEM for a given location.")
@discord.app_commands.describe(zipcode="The 5-digit ZIP code for the map's center.",
                               state="The 2-letter state abbreviation for the map's area.",
                               time="The time for the radar image (defaults to 'latest').")
@discord.app_commands.autocomplete(state=state_autocomplete)
async def iemradmap(interaction: discord.Interaction, zipcode: str = None, state: str = None, time: str = "latest"):
    if not zipcode and not state:
        await interaction.response.send_message("Please provide either a ZIP code or a state abbreviation.", ephemeral=True)
        return
    if zipcode and state:
        await interaction.response.send_message("Please provide either a ZIP code or a state, not both.", ephemeral=True)
        return

    await interaction.response.defer()

    # Construct the base URL
    base_radmap_url = "https://mesonet.agron.iastate.edu/GIS/radmap.php"
    params = {
        'layers[]': 'nexrad',
        'width': 640,
        'height': 480,
    }
    title_location = ""
    filename_part = ""

    if zipcode:
        if not zipcode.isdigit() or len(zipcode) != 5:
            await interaction.followup.send("Please enter a valid 5-digit ZIP code.")
            return

        loc_data = await get_location_from_zip(zipcode)
        if not loc_data:
            await interaction.followup.send(f"Could not find location for ZIP code: {zipcode}")
            return

        lat = float(loc_data['lat'])
        lon = float(loc_data['lon'])
        params['bbox'] = f"{lon - 1.5},{lat - 1.5},{lon + 1.5},{lat + 1.5}"
        title_location = f"{loc_data['city']}, {loc_data['state']} ({zipcode})"
        filename_part = zipcode
    
    elif state:
        state_code = state.upper()
        state_name = US_STATES.get(state_code)
        if not state_name:
            await interaction.followup.send("Please enter a valid 2-letter US state or territory abbreviation.")
            return
        params['sector'] = state_code
        title_location = f"State of {state_name}"
        filename_part = state_code

    if time != "latest":
        params['ts'] = time
    
    request_url = requests.Request('GET', base_radmap_url, params=params).prepare().url

    try:
        response = await bot.loop.run_in_executor(None, lambda: requests.get(request_url, timeout=15))
        response.raise_for_status()

        if 'image/png' not in response.headers.get('Content-Type', ''):
            await interaction.followup.send("The API did not return an image. Please try again later.")
            return

        filename = f"radmap_{filename_part}_{time}.png"
        filepath = settings.BASE_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)

        file = discord.File(filepath, filename=filename)
        embed = discord.Embed(title=f"IEM Radar Map for {title_location}", color=discord.Color(0xffffff))
        embed.set_thumbnail(url="https://files.catbox.moe/uc137x.png")
        embed.set_image(url=f"attachment://{filename}")

        time_display = "Latest" if time == "latest" else f"UTC {time[8:10]}:{time[10:12]} on {time[4:6]}/{time[6:8]}/{time[0:4]}"
        embed.set_footer(text=f"Time: {time_display} | Provided by Iowa Environmental Mesonet")

        await interaction.followup.send(embed=embed, file=file)
    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"Failed to fetch radar image: {e}")
    finally:
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)

@iemradmap.autocomplete('time')
async def iemradmap_time_autocomplete(interaction: discord.Interaction, current: str) -> list[discord.app_commands.Choice[str]]:
    choices = [discord.app_commands.Choice(name="Latest", value="latest")]
    now = datetime.datetime.utcnow()
    
    # Round down to the nearest 5 minutes
    start_minute = (now.minute // 5) * 5
    rounded_now = now.replace(minute=start_minute, second=0, microsecond=0)
    
    for i in range(12): # Last 3 hours in 15 min increments
        dt = rounded_now - datetime.timedelta(minutes=i * 15)
        time_str = dt.strftime("%Y%m%d%H%M")
        display_str = dt.strftime("%H:%M UTC on %Y-%m-%d")
        choices.append(discord.app_commands.Choice(name=display_str, value=time_str))

    return [choice for choice in choices if current.lower() in choice.name.lower()][:25]

def check_for_updates():
    """Checks for updates from GitHub and auto-updates if needed."""
    try:
        # Check if inside a git repository
        subprocess.check_output(["git", "rev-parse", "--is-inside-work-tree"], stderr=subprocess.DEVNULL)
        
        print("Checking for updates...")
        subprocess.check_call(["git", "fetch"])
        
        local_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode('utf-8')
        try:
            remote_commit = subprocess.check_output(["git", "rev-parse", "@{u}"]).strip().decode('utf-8')
        except subprocess.CalledProcessError:
            # Fallback: try origin/main if upstream not configured
            remote_commit = subprocess.check_output(["git", "rev-parse", "origin/main"]).strip().decode('utf-8')
            
        if local_commit != remote_commit:
            print("Update found! Downloading latest version...")
            subprocess.check_call(["git", "pull"])
            
            is_windows = os.name == 'nt'
            pip_cmd = "pip" if is_windows else "pip3"
            python_cmd = "python" if is_windows else "python3"
            
            print(f"Installing requirements with {pip_cmd}...")
            subprocess.check_call([pip_cmd, "install", "-r", "requirements.txt"])
            
            print(f"Restarting bot with {python_cmd}...")
            os.execvp(python_cmd, [python_cmd, "main.py"])
        else:
            print("Bot is up to date.")
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Skipping update check (not a git repo or git not found).")
    except Exception as e:
        print(f"Update check failed: {e}")

# --- Run Bot ---
if __name__ == "__main__":
    check_for_updates()
    if not settings.DISCORD_TOKEN or settings.DISCORD_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: DISCORD_TOKEN not found or not set in .env file.")
    else:
        bot.run(settings.DISCORD_TOKEN)