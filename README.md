# anki-jlpt

## Running this Locally

```bash
$ cd anki-jlpt/
$ luigi --module deck jlpt.SaveAsAnkiDeck --local-scheduler
```

Note that deck needs to be in your `PYTHONPATH`, or else this can produce an error (`ImportError: No module named 'deck'`). Add the current working directory to the command `PYTHONPATH` with:

```bash
$ PYTHONPATH='.' luigi --module deck jlpt.SaveAsAnkiDeck --local-scheduler
```
