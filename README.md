<p align="center">
  <img width="1640" height="664" alt="New Project" src="https://github.com/user-attachments/assets/ffabac5c-ea22-4eec-930b-8b20390f8de6" />
</p>

# about

Emer is a full open source remake of a previous old project dev1 made back in 2024/2025. it is a eas tracker and weather/eas utility bot and you can use this in any server.


this follows the GPL-3.0 license so be fair with the project


feedback. pull requests and issues reported would be gladly appreciated!


windows only tested. not sure about linux or mac os and ffmpeg for audio may not work on those two :/


# how 2 setup the discord bot


## prerequisites
python installed on your system.

## installation
1. download the source code/git clone this repository.
2. open a terminal in the project folder.
3. install the required libraries by running:
   ```bash
   pip install -r requirements.txt
   ```

## configuration
1. find the file named `env.rename` in the folder.
2. rename it to `.env`.
3. open the `.env` file in a text editor.
4. paste your discord bot token in `DISCORD_TOKEN`.
5. paste your server id in `SERVER_ID`.
6. paste the channel id where you want alerts to go in `CHANNEL_ID`.
7. paste a role id in `ROLE_ID` if you want pings, or leave it blank.
8. make sure all intents in the bot tab are enabled

## custom stations setup.
to add radio stations, edit the `stations.txt` file.
add one station per line in this format:
```text
station_name stream_url
```
example:
```text
WJON WeatherScan https://radio.wjonip.org/WJON-WSCN
```

## start bot
start the bot by running:
```bash
python main.py
```

## examples/preview
EAS tracker example:

<img width="615" height="330" alt="image" src="https://github.com/user-attachments/assets/0138b1ca-17e9-41e3-a2ea-755287e18e9e" />

search query example for tornado:

<img width="615" height="457" alt="image" src="https://github.com/user-attachments/assets/8429b0ae-be22-47e7-a860-22fd049af58e" />

anti-troll:

<img width="617" height="369" alt="image" src="https://github.com/user-attachments/assets/5c6f1d0a-1efc-4a4f-ad54-fd57a8aa5614" />

active example:

<img width="663" height="255" alt="image" src="https://github.com/user-attachments/assets/a15f6fb5-0105-4816-a848-210b379af077" />

station list example:

<img width="1053" height="304" alt="image" src="https://github.com/user-attachments/assets/02f677ec-c118-46ad-9d5e-66410df9ea30" />

weather radio control example:

<img width="476" height="203" alt="image" src="https://github.com/user-attachments/assets/9e44d6e4-f23b-44d7-bbd3-d27e71b6d32f" />

NWS forecast example:

<img width="638" height="345" alt="image" src="https://github.com/user-attachments/assets/3e842a34-314c-45f7-b227-f883adf7a34e" />


and many more!
