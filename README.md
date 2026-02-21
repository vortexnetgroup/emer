<p align="center">
  <img width="1640" height="664" alt="New Project" src="https://github.com/user-attachments/assets/ffabac5c-ea22-4eec-930b-8b20390f8de6" />
</p>

# about

Emer is a full open source remake of a previous old project dev1 made back in 2024/2025. it is a eas tracker and weather/eas utility bot and you can use this in any server.


this follows the GPL-3.0 license so be fair with the project


feedback. pull requests and issues reported would be gladly appreciated!


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
