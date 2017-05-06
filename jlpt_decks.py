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


if __name__ == '__main__':
    luigi.run(['twitter.GetTweets', '--workers', '1', '--local-scheduler'])
