import re
import json
import datetime
import luigi
import tweepy


class GetTweets(luigi.Task):
    """
    Generates a local file containing chosen fields of Twitter
    API response in JSON format
    """
    task_namespace = 'twitter'
    date = luigi.DateParameter(default=datetime.date.today())

    # Generate an OAuth access token @ https://apps.twitter.com/
    API_KEY = 'consumer_key'
    API_SECRET = 'consumer_secret'
    ACCESS_TOKEN = 'access_token'
    ACCESS_TOKEN_SECRET = 'access_token_secret'

    auth = tweepy.OAuthHandler(consumer_key=API_KEY,
                               consumer_secret=API_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)
    # Specifies the id or screen name of the user.
    screen_name = 'screen_name'

    def output(self):
        return luigi.LocalTarget(
            path='/tmp/_%s-%s.ldj' % (self.screen_name, self.date)
        )

    def run(self):
        with self.output().open('w') as outfile:
            for status in tweepy.Cursor(self.api.user_timeline,
                                        id=self.screen_name).items():
                outfile.write(
                    json.dumps(
                        {
                            'id_str': status.id_str,
                            'created_at': status.created_at.isoformat(),
                            'screen_name': status.user.screen_name,
                            'text': status.text
                        },
                        ensure_ascii=False
                    )
                )
                outfile.write('\n')


class ProcessTweets(luigi.Task):
    """
    Generates a local file to be written to a database for persistent
    storage after cleaning up the tweets
    """
    task_namespace = 'twitter'
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        return GetTweets()

    def output(self):
        return luigi.LocalTarget(
            path='/tmp/_processed_tweets-%s.ldj' % self.date
        )

    @staticmethod
    def _tidy(question):
        item = dict()
        pattern = re.compile(
            pattern=r'([a-zA-Z])\s?\.?\s?(.*?)(?=[a-zA-Z]|$)',
            flags=re.IGNORECASE
        )
        ques = question.strip()
        # Check if options are available for the question
        index = ques.rfind('A')
        if index == -1:
            stem = re.sub(pattern=r'\s+', repl=' ', string=ques.strip())
            item.update({'stem': stem})
            return item
        # Clean up options as key: value pairs
        stem = re.sub(pattern=r'\s+', repl=' ', string=ques[:index].strip())
        item.update({'stem': stem})
        options = ques[index:].strip()
        options = dict(pattern.findall(string=options))
        item.update(
            {'options': {k.strip(): v.strip() for k, v in options.items()}}
        )
        return item

    def run(self):
        # An item bank to function as a repository of test items
        item_bank = list()
        # `characters` and regex `pattern` to check
        # the presence of in a tweet
        characters = '◇◆'
        pattern = re.compile(r'([^◇◆]+)', flags=re.IGNORECASE)

        with self.input().open('r') as fobj:
            for t in fobj.readlines():
                tweet = json.loads(s=t)
                text = tweet.get('text')
                if text and any(char in text for char in characters):
                    question, answer = pattern.findall(string=text)
                    key = answer.strip()
                    # Clean up `question`
                    item = self._tidy(question=question)
                    options = item.get('options')
                    if options and options.get(key):
                        item.update(
                            {'key': '{key_index}. {key}'
                                .format(key_index=key, key=options.get(key))}
                        )
                    else:
                        item.update({'key': key})
                    item.update(tweet)
                    item_bank.append(item)

        # Write `item_bank` to line delimited JSON
        with self.output().open('w') as outfile:
            for item in item_bank:
                outfile.write(json.dumps(item, ensure_ascii=False))
                outfile.write('\n')


if __name__ == '__main__':
    luigi.run(['twitter.GetTweets', '--workers', '1', '--local-scheduler'])
