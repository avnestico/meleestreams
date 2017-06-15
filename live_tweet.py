from twython import TwythonError


def retweet(tweet, client):
    try:
        client.retweet(id=tweet["id"])
        print("RT:", tweet["text"])
    except TwythonError as e:
        print(e)


def unretweet(tweet, client):
    try:
        client.post('statuses/unretweet/%s' % tweet["id"])
        print("URT:", tweet["text"])
    except TwythonError as e:
        print(e)
