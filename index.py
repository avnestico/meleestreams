from __future__ import print_function

import os

import requests
from datetime import datetime
from twython import Twython
from twython.exceptions import TwythonError
from urlparse import urlparse

consumer_key = os.environ["consumer_key"]
consumer_secret = os.environ["consumer_secret"]
access_token_key = os.environ["access_token_key"]
access_token_secret = os.environ["access_token_secret"]
client_id = os.environ["client_id"]

client = Twython(consumer_key, consumer_secret, access_token_key, access_token_secret)

MINUTE_DELAY = 15


def handler(event, context):
    results = client.get_home_timeline(count=200)
    print("found", str(len(results)), "tweets")

    r = requests.get('https://api.twitch.tv/kraken/streams/?game=Super%20Smash%20Bros.%20Melee',
                     headers={'Accept': 'application/vnd.twitchtv.v5+json',
                              'Client-ID': client_id})
    stream_dict = r.json()

    channels = []
    for stream in stream_dict["streams"]:
        channels.append(stream["channel"]["name"])
    print(channels)

    for tweet in results:
        try:
            media_url = tweet["entities"]["urls"][0]["expanded_url"]
            parsed = urlparse(media_url)
            netloc = parsed[1]
            path = parsed[2].replace("/", "")
            if netloc.endswith("twitch.tv") and path in channels:
                created_at = datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y")
                tdelta = datetime.now() - created_at
                if tdelta.seconds <= MINUTE_DELAY * 60:
                    try:
                        client.retweet(id=tweet["id"])
                    except TwythonError as e:
                        print(e)

        except (KeyError, IndexError):
            pass

if __name__ == "__main__":
    handler(None, None)
