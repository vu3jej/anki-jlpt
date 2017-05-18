# anki-jlpt
A set of [Luigi](https://github.com/spotify/luigi) pipelines to collect, clean and transform tweets to [Anki](https://apps.ankiweb.net/) decks

## Limitations

This code works with the following Twitter accounts as of `2017-05-18T08:55:12.787058`:

* [jlpt_n5](https://twitter.com/jlpt_n5)
* [jlpt_n4](https://twitter.com/jlpt_n4)
* [jlpt_n3](https://twitter.com/jlpt_n3)
* [jlpt_n2](https://twitter.com/jlpt_n2)
* [jlpt_n1](https://twitter.com/jlpt_n1)

## Running this Locally

```bash
$ cd anki-jlpt/
$ luigi --module deck jlpt.SaveAsAnkiDeck --local-scheduler
```

Note that deck needs to be in your `PYTHONPATH`, or else this can produce an error (`ImportError: No module named 'deck'`). Add the current working directory to the command `PYTHONPATH` with:

```bash
$ PYTHONPATH='.' luigi --module deck jlpt.SaveAsAnkiDeck --local-scheduler
```
