import io
import json
import os
import unittest

import datetime
from mock import patch, Mock

import index


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
    @unittest.skip("Don't need to export data")
    def test_export(self):
        my_tweets, following_tweets, channels = index.get_data()
        print(channels)
        export_data("my_tweets.txt", my_tweets)
        export_data("following_tweets.txt", following_tweets)
        export_data("channels.txt", channels)

    def test_open(self):
        _, ft, c = import_data(par="retweet")
        assert "http://twitch.tv/showdowngg" in index.get_tweet_urls(ft[0])
        assert c[0] == "showdowngg"

    @patch('index.retweet', side_effect=mock_retweet)
    def test_retweet(self, mock2):
        index.curr_time = datetime.datetime(year=2017, month=6, day=14, hour=3, minute=5)
        mt, ft, c = import_data("retweet")
        index.retweet_tweets(mt, ft, c)
        Mock.assert_called_once(mock2)

    @patch('index.retweet', side_effect=mock_retweet)
    def test_dont_retweet_old(self, mock2):
        index.curr_time = datetime.datetime(year=2017, month=6, day=14, hour=3, minute=25)
        mt, ft, c = import_data("retweet")
        index.retweet_tweets(mt, ft, c)
        Mock.assert_not_called(mock2)

    @patch('index.retweet', side_effect=mock_retweet)
    def test_dont_retweet_dead(self, mock2):
        index.curr_time = datetime.datetime(year=2017, month=6, day=14, hour=3, minute=5)
        mt, ft, c = import_data("dont_retweet")
        index.retweet_tweets(mt, ft, c)
        Mock.assert_not_called(mock2)

    @patch('index.retweet', side_effect=mock_retweet)
    def test_dont_retweet_already_rtd(self, mock2):
        index.curr_time = datetime.datetime(year=2017, month=6, day=16, hour=20, minute=30)
        mt, ft, c = import_data("dont_retweet_already_rtd")
        index.retweet_tweets(mt, ft, c)
        Mock.assert_not_called(mock2)

    @patch('index.unretweet', side_effect=mock_unretweet)
    @patch('index.tweet_age', return_value=datetime.timedelta(seconds=30))
    def test_unretweet(self, _, mock2):
        mt, _, c = import_data("unretweet")
        index.unretweet_tweets(mt, c)
        Mock.assert_called_once(mock2)

    @patch('index.unretweet', side_effect=mock_unretweet)
    @patch('index.tweet_age', return_value=datetime.timedelta(minutes=30))
    def test_keep_retweet_old(self, _, mock2):
        mt, _, c = import_data("unretweet")
        index.unretweet_tweets(mt, c)
        Mock.assert_not_called(mock2)

    @patch('index.unretweet', side_effect=mock_unretweet)
    @patch('index.tweet_age', return_value=datetime.timedelta(seconds=30))
    def test_keep_retweet_live(self, _, mock2):
        mt, _, c = import_data("keep_retweet")
        index.unretweet_tweets(mt, c)
        Mock.assert_not_called(mock2)

    @patch('index.retweet', side_effect=mock_retweet)
    @patch('index.unretweet', side_effect=mock_unretweet)
    def test_retweet_compound(self, _, mock2):
        index.curr_time = datetime.datetime(year=2017, month=6, day=14, hour=2, minute=20)
        mt, ft, c = import_data("compound")
        index.retweet_tweets(mt, ft, c)
        Mock.assert_called_once_with(mock2, ft[1], index.client)

    @patch('index.retweet', side_effect=mock_retweet)
    @patch('index.unretweet', side_effect=mock_unretweet)
    def test_dont_retweet_compound(self, _, mock2):
        index.curr_time = datetime.datetime(year=2017, month=6, day=14, hour=2, minute=0)
        mt, ft, c = import_data("compound")
        index.retweet_tweets(mt, ft, c)
        Mock.assert_not_called(mock2)


if __name__ == '__main__':
    unittest.main()
