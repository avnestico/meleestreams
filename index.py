from __future__ import print_function

import os
from datetime import datetime, timedelta
from urlparse import urlparse

import requests
from twython import Twython

from live_tweet import retweet, unretweet

game = "Super%20Smash%20Bros.%20Melee"
username = "meleestreams"

consumer_key = os.environ["consumer_key"]
consumer_secret = os.environ["consumer_secret"]
access_token_key = os.environ["access_token_key"]
access_token_secret = os.environ["access_token_secret"]
client_id = os.environ["client_id"]
client = Twython(consumer_key, consumer_secret, access_token_key, access_token_secret)
valid_netlocs = ["twitch.tv", "www.twitch.tv", "m.twitch.tv"]

RETWEET_WINDOW_MINS = 15
URL_LOCKOUT_WINDOW_MINS = 60

curr_time = datetime.utcnow()


def get_twitch_channels():
    channels = []
    r = requests.get('https://api.twitch.tv/kraken/streams/?game=%s' % game,
                     headers={'Accept':    'application/vnd.twitchtv.v5+json',
                              'Client-ID': client_id})
    stream_dict = r.json()
    for stream in stream_dict["streams"]:
        channels.append(stream["channel"]["name"])
    return channels


def get_retweeted_tweets():
    curr_tweets = client.get_user_timeline(screen_name=username, count=200, include_rts=True)
    return curr_tweets


def get_following_tweets():
    results = client.get_home_timeline(count=200, exclude_replies=False)
    print("Found", str(len(results)), "tweets")
    return results


def tweet_age(tweet):
    created_at = datetime.strptime(tweet["created_at"], "%a %b %d %H:%M:%S +0000 %Y")
    tdelta = curr_time - created_at
    return tdelta


def get_tweet_urls(tweet):
    media_urls = []
    url_list = tweet["entities"]["urls"]
    for url in url_list:
        media_urls.append(url["expanded_url"])
    return media_urls


def get_all_tweet_urls(tweets, limit_age=False):
    max_age = timedelta(seconds=URL_LOCKOUT_WINDOW_MINS * 60) if limit_age else datetime.max
    media_urls = []
    for tweet in tweets:
        if tweet_age(tweet) < max_age:
            media_urls.extend(get_tweet_urls(tweet))
    return media_urls


def most_liked_tweet(tweets):
    if tweets:
        tweets.sort(key=lambda tweet: tweet["id"], reverse=True)
        tweets.sort(key=lambda tweet: tweet["favorite_count"], reverse=True)
        return tweets[0]


def should_rt(tweet, channels):
    media_urls = get_tweet_urls(tweet)
    for media_url in media_urls:
        parsed = urlparse(media_url)
        netloc = parsed[1].lower()
        path = parsed[2].replace("/", "")
        if netloc in valid_netlocs and path in channels:
            return True
    return False


def retweet_oldest_first(tweets):
    tweets.sort(key=lambda tweet: tweet["id"])
    for tweet in tweets:
        retweet(tweet, client)


def unretweet_tweets(mt, channels):
    for tweet in mt:
        if tweet_age(tweet).total_seconds() <= RETWEET_WINDOW_MINS * 60:
            if not should_rt(tweet, channels):
                unretweet(tweet, client)


def retweet_tweets(mt, ft, channels):
    retweeted_urls = get_all_tweet_urls(mt, limit_age=True)

    retweet_d = {}
    for tweet in ft:
        if tweet_age(tweet).total_seconds() <= RETWEET_WINDOW_MINS * 60 and should_rt(tweet, channels):
            media_urls = get_tweet_urls(tweet)
            for url in media_urls:
                if url not in retweeted_urls:
                    if url not in retweet_d:
                        retweet_d[url] = []
                    retweet_d[url].append(tweet)

    to_retweet = []
    for url in retweet_d:
        chosen_tweet = most_liked_tweet(retweet_d[url])
        if chosen_tweet:
            to_retweet.append(chosen_tweet)
    retweet_oldest_first(to_retweet)


def get_data():
    my_tweets = get_retweeted_tweets()
    following_tweets = get_following_tweets()
    channels = get_twitch_channels()

    return my_tweets, following_tweets, channels


def handler(event, context):
    my_tweets, following_tweets, channels = get_data()

    unretweet_tweets(my_tweets, channels)
    retweet_tweets(my_tweets, following_tweets, channels)


if __name__ == "__main__":
    handler(None, None)
