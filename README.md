# RogueFishLives

A configurable twitter bot built in python3 for sending out real time alerts when one of a group of tracked twitch.tv streamers goes live.

### Requires:

`pip install python-twitch-client python-twitter`

### Usage:

The basic usage is to:

1. Apply for a twitter project and get the consumer and access information for the new account. Add this info into the config.yaml template included in this repo.

2. Get your [Twitch OAuth Token and Client ID](https://twitchapps.com/tokengen/) and add that to config.yaml

3. Use the `--usernames` argument to generate a YAML-formatted list of twitch streamers and their required twitch info for pasting into the sample config.yaml file.

4. From here you can launch the bot with `python3 main.py config.yaml` or use the included systemd service file to turn it into a restarting service.

`$ python3 main.py -h`
```
usage: main.py [-h] [--usernames [USERNAMES [USERNAMES ...]]] [config]

Track Twitch streams and posts alerts to twitter.

positional arguments:
  config                Bot configuration file in YAML format.

optional arguments:
  -h, --help            show this help message and exit
  --usernames [USERNAMES [USERNAMES ...]], -u [USERNAMES [USERNAMES ...]]
                        Convert a space-separated list of Twitch usernames
                        into channel IDs for pasting into config.yaml.
```
