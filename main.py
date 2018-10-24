import argparse
import logging.config
import logging
from yaml import load
from time import gmtime, strftime, sleep
from random import choice
from twitch import TwitchClient
from mastodon import Mastodon
import twitter

# The Set for storing the active state of live streamers
prevStreams = set()
# program config, to be loaded from a user-provided YAML setting file
config = {}


def main():
    global config
    # setup and parse input arguments
    parser = argparse.ArgumentParser(description='Track Twitch streams and \
posts alerts to twitter.')
    parser.add_argument('config',
                        nargs='?',
                        default='config.yaml',
                        help='Bot configuration file in YAML format.')
    parser.add_argument('--usernames', '-u',
                        nargs="*",
                        help='Convert a space-separated list of Twitch \
usernames into channel IDs for pasting into config.yaml.')
    args = parser.parse_args()

    with open(args.config, 'r') as f:
        config = load(f)

    # setup logging using the settings in the provided YAML config
    logging.config.dictConfig(config['logging'])

    logging.info("Config loaded!")

    if args.usernames:
        logging.debug('Usernames provided!')
        print_ids(args.usernames)
        exit()

    while True:
        # update the config dict so we can do live updating
        logging.info('Reloading config from file..')
        with open(args.config, 'r') as f:
            config = load(f)
        check_streams()
        logging.info("sleeping...")
        sleep(config['polling_interval'])


def check_streams():
    global config, prevStreams

    logging.info("Checking streams...")
    try:
        client = TwitchClient(config['twitch']['client_id'],
                              config['twitch']['oauth_token'])
        # concatenate the list of channel IDs into a Twitch API query string
        query = ','.join([str(i) for i in config['streamers'].keys()])
        # get the list of live streams and convert it into a Set of ids
        results = client.streams.get_live_streams(query)
    except Exception as e:
        logging.error("Fatal Twitch API exception!")
        logging.error(e)
        return
    # create a dict mapping channel IDs to games
    games = {i['channel']['id']: i['game'] for i in results}
    currentStreams = set(i['channel']['id'] for i in results)

    logging.debug('Current streams: {}'.format(currentStreams))

    # use Set logic to find out the difference between the last check and now
    ended, started = set(), set()
    if config['send_end']:
        ended = prevStreams - currentStreams
    if config['send_start']:
        started = currentStreams - prevStreams

    logging.debug('Started streams: {0}, \
Ended streams: {1}'.format(started, ended))

    # iterate over both lists and send out messages with the event formattings
    for i in started:
        message = format_tweet(i, config['tweet_format']['stream_start'],
                               games[i])
        if 'twitter' in config:
            send_tweet(message)
        if 'mastodon' in config:
            send_toot(message)

    for i in ended:
        message = format_tweet(i, config['tweet_format']['stream_end'])
        if 'twitter' in config:
            send_tweet(message)
        if 'mastodon' in config:
            send_toot(message)

    # update the state for next check
    prevStreams = currentStreams


def format_tweet(user_id, template_options, game=None):
    '''
        Given a twitch user id and a list of tweet string templates,
        pick a random tweet template and fill it with details from the
        given user and return it.
    '''
    global config

    # get the dictionary for the specified user from the config
    user = config['streamers'][user_id]
    time = strftime('%H:%M', gmtime())
    # pick a random end tweet template and fill it with user details
    tweet = choice(template_options).format(time=time,
                                            display_name=user['display_name'],
                                            name=user['name'], game=game)
    logging.debug("Final Tweet: " + tweet)
    return tweet


def print_ids(usernames):
    '''
        Given a list of Twich usernames, pretty print their channel
        information in YAML format for pasting into the config.yaml file's
        streamer section.
    '''
    global config

    try:
        client = TwitchClient(config['twitch']['client_id'],
                              config['twitch']['oauth_token'])
        users = client.users.translate_usernames_to_ids(usernames)
    except Exception as e:
        logging.error("Fatal Twitch API error!")
        logging.error(e)
        return
    print("Copy and Paste the output below into your config.yaml file. \n")
    print('streamers:')
    for u in users:
        print('  {0}:'.format(u['id']))
        print('    name: {0}'.format(u['name']))
        print('    display_name: {0}'.format(u['display_name']))


def send_tweet(msg):
    '''
        Take the given message and tweet it out using app creds provided in the
        config settings.
    '''
    global config
    logging.info("Sending tweet: " + msg)
    api = twitter.Api(
        consumer_key=config['twitter']['consumer_key'],
        consumer_secret=config['twitter']['consumer_secret'],
        access_token_key=config['twitter']['access_token_key'],
        access_token_secret=config['twitter']['access_token_secret'])
    try:
        status = api.PostUpdate(msg)
    except UnicodeDecodeError:
        logging.error("The message could not be encoded.")
    except twitter.error.TwitterError as e:
        logging.error(e)
        status = "Tweet not sent!"
        pass
    logging.debug(status)


def send_toot(msg):
    global config
    logging.info("Sending toot: " + msg)
    mastodon = Mastodon(
        api_base_url=config['mastodon']['api_base_url'],
        client_id=config['mastodon']['client_key'],
        client_secret=config['mastodon']['client_secret'],
        access_token=config['mastodon']['access_token']
    )
    try:
        status = mastodon.status_post(msg)
    except Exception as e:
        logging.error(e)
        status = "Tweet not sent!"
        pass
    logging.debug(status)


if __name__ == '__main__':
    main()
