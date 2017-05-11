"""
Write configuration values to file. Works with `configobj`.
"""
from os.path import abspath, dirname, join
from configobj import ConfigObj

_FILENAME = join(dirname(abspath(__file__)), 'config.ini')


def configure():
    """
    Add configuration values and write to disk    
    """
    config = ConfigObj()
    config.filename = _FILENAME

    twitter = {
        'consumer_key': '',
        'consumer_secret': '',
        'access_token': '',
        'access_token_secret': '',
        'screen_name': ''
    }
    config.update({'twitter': twitter})
    config.write()


if __name__ == '__main__':
    configure()
