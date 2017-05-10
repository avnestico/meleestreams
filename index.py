from __future__ import print_function

import os

from datetime import datetime
from urlparse import urlparse

import requests
from twython import Twython, TwythonError

consumer_key = os.environ["consumer_key"]
consumer_secret = os.environ["consumer_secret"]
access_token_key = os.environ["access_token_key"]
access_token_secret = os.environ["access_token_secret"]
client_id = os.environ["client_id"]

client = Twython(consumer_key, consumer_secret, access_token_key, access_token_secret)

valid_netlocs = ["twitch.tv", "www.twitch.tv", "m.twitch.tv"]
MINUTE_DELAY = 15


def get_channels(stream_dict):
    channels = []
    for stream in stream_dict["streams"]:
        channels.append(stream["channel"]["name"])
    print(channels)
    return channels


def get_urls(url_list):
    media_urls = []
    for url in url_list:
        media_urls.append(url["expanded_url"])
    return media_urls


def handler(event, context):
    results = client.get_home_timeline(count=200, exclude_replies=False)
    print("Found", str(len(results)), "tweets")

    curr_time = datetime.utcnow()

    r = requests.get('https://api.twitch.tv/kraken/streams/?game=Super%20Smash%20Bros.%20Melee',
                     headers={'Accept':    'application/vnd.twitchtv.v5+json',
                              'Client-ID': client_id})
    channels = get_channels(r.json())

    for tweet in results[::-1]:
        created_at = datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y")
        tdelta = curr_time - created_at

        if tdelta.total_seconds() <= MINUTE_DELAY * 60:
            rt_status = False
            media_urls = get_urls(tweet["entities"]["urls"])

            for media_url in media_urls:
                parsed = urlparse(media_url)
                netloc = parsed[1].lower()
                path = parsed[2].replace("/", "")
                if netloc in valid_netlocs and path in channels:
                    rt_status = True

            try:
                if rt_status:
                    client.retweet(id=tweet["id"])
                    print("RT:", media_urls)
                elif media_urls:
                    client.post('statuses/unretweet/%s' % tweet["id"])
                    print("URT:", media_urls)
            except TwythonError as e:
                print(e)


if __name__ == "__main__":
    handler(None, None)
