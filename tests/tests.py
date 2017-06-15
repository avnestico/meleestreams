import io
import json
import os
import unittest

import datetime
import mock

import index
import live_tweet
import dry_run


def export_data(file, data):
    with io.open(file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False))


def file_import(file, par=""):
    path = os.path.join(par, file)
    with open(path, "r") as f:
        data = json.load(f, encoding='utf-8')
    return data


def import_data(par=""):
    mt = file_import("my_tweets.txt", par=par)
    ft = file_import("following_tweets.txt", par=par)
    c = file_import("channels.txt", par=par)
    return mt, ft, c


def mock_retweet(tweet, _):
    print("Dry RT:", tweet["text"])


def mock_unretweet(tweet, _):
    print("Dry URT:", tweet["text"])


class TestTweets(unittest.TestCase):
    @unittest.skip("Data export")
    def test_export(self):
        my_tweets, following_tweets, channels = index.get_data()
        print(channels)
        export_data("mt.txt", my_tweets)
        export_data("ft.txt", following_tweets)
        export_data("ch.txt", channels)

    def test_open(self):
        _, ft, c = import_data(par="retweet")
        assert "http://twitch.tv/showdowngg" in index.get_tweet_urls(ft[0])
        assert c[0] == "showdowngg"

    @mock.patch('index.retweet', side_effect=mock_retweet)
    @mock.patch('index.tweet_age', value=datetime.timedelta(seconds=30))
    def test_retweet(self, mock1, mock2):
        mt, ft, c = import_data("retweet")
        index.retweet_tweets(mt, ft, c)
        mock.Mock.assert_called_once(mock1)

    def test_unretweet(self):
        pass

if __name__ == '__main__':
    unittest.main()
