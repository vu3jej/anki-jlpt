import re
import json
import datetime
from collections import OrderedDict
from os.path import abspath, dirname, join
# third party
import luigi
import tweepy
import genanki
import pystache
from configobj import ConfigObj

config = ConfigObj(infile=join(dirname(abspath(__file__)), 'config.ini'))
twitter = config['twitter']

API_KEY = twitter['consumer_key']
API_SECRET = twitter['consumer_secret']
ACCESS_TOKEN = twitter['access_token']
ACCESS_TOKEN_SECRET = twitter['access_token_secret']
SCREEN_NAME = twitter['screen_name']


class GetTweets(luigi.Task):
    """
    Generates a local file containing chosen fields of Twitter
    API response in JSON format
    """
    task_namespace = 'twitter'
    date = luigi.DateParameter(default=datetime.date.today())

    auth = tweepy.OAuthHandler(consumer_key=API_KEY,
                               consumer_secret=API_SECRET)
    auth.set_access_token(key=ACCESS_TOKEN, secret=ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    def output(self):
        return luigi.LocalTarget(
            path='/tmp/_%s-%s.ldj' % (SCREEN_NAME, self.date)
        )

    def run(self):
        with self.output().open('w') as outfile:
            for status in tweepy.Cursor(self.api.user_timeline,
                                        id=SCREEN_NAME).items():
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
            return {'stem': stem}

        # Clean up options as key: value pairs
        options = ques[index:].strip()
        options = dict(pattern.findall(string=options))
        if len(options) < 4:
            stem = re.sub(pattern=r'\s+', repl=' ', string=ques.strip())
            item.update({'stem': stem})
        else:
            stem = re.sub(pattern=r'\s+', repl=' ',
                          string=ques[:index].strip())
            item.update({
                'stem': stem,
                'options': {k.strip(): v.strip() for k, v in options.items()}
            })
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


class SaveAsAnkiDeck(luigi.Task):
    task_namespace = 'twitter'
    date = luigi.DateParameter(default=datetime.date.today())

    jlpt_deck = genanki.Deck(deck_id=1498953600, name='jlpt')
    jlpt_model = genanki.Model(
        model_id=112,
        name='Japanese',
        css='{.answer {text-align: center;}}',
        fields=[
            {'name': 'stem'},
            {'name': 'options'},
            {'name': 'key'}
        ],
        templates=[
            {
                'name': 'with_options',
                'qfmt': '{{stem}}<br>{{options}}',
                'afmt': '{{FrontSide}}'
                        '<hr id="answer">'
                        '<p><span class="answer">{{key}}</span></p>'
            },
            {
                'name': 'without_options',
                'qfmt': '{{stem}}',
                'afmt': '{{FrontSide}}'
                        '<hr id="answer">'
                        '<p><span class="answer">{{key}}</span></p>'
            }
        ]
    )

    def requires(self):
        return ProcessTweets()

    def output(self):
        return luigi.LocalTarget(
            path='/tmp/_anki_deck-%s.apkg' % self.date
        )

    def run(self):
        with self.input().open('r') as fobj:
            for row in fobj.readlines():
                item = json.loads(s=row)
                options = item.get('options')
                if options:
                    template = '{{#options}}{{k}}. {{v}}<br>{{/options}}'
                    options = OrderedDict(sorted(options.items()))
                    listcomp = [{'k': k, 'v': v} for k, v in options.items()]
                    options_rendered = pystache.render(
                        template=template,
                        context={'options': listcomp}
                    )
                    note = genanki.Note(
                        model=self.jlpt_model,
                        fields=[item.get('stem'), options_rendered,
                                item.get('key')]
                    )
                    pass
                else:
                    note = genanki.Note(
                        model=self.jlpt_model,
                        fields=[item.get('stem'), '', item.get('key')]
                    )
                self.jlpt_deck.add_note(note=note)

        genanki.Package(deck_or_decks=self.jlpt_deck).write_to_file(
            file=self.output().path
        )


if __name__ == '__main__':
    luigi.run(['twitter.GetTweets', '--workers', '1', '--local-scheduler'])
