#!/usr/bin/env python
'''Post a message to Slack.

Useful when you run commands automatically, e.g. in a crontab, and you need
a feedback from the execution.

The script can run in three modes:
 1. simple mode, posting a message to a channel;
 2. exit status mode, posting a message and the exit status (that you need to
    provide using the `--exit-status` to the script) to a channel;
 3. [TBD] wrap mode, posting a message, the status code, stderr and stdout, and
    the execution time to a channel.

The script uses "Incoming Webhooks" by Slack, you can find more info about
some of the params here:
 - https://api.slack.com/incoming-webhooks

'''

import argparse
import json
import os
import platform
from urllib2 import urlopen


def prepare_text_error(args):
    if args.text_error:
        return args.text_error

    return u'FAILURE: {}'.format(args.text)


def prepare_icon(icon_name):
    return u':{}:'.format(icon_name)


def prepare_data(args):
    payload = {
        'channel': args.channel,
        'username': args.username,
        'text': args.text,
        'icon_emoji': prepare_icon(args.icon_emoji)
    }

    if args.exit_status is not None and args.exit_status != 0:
        payload.update({
            'text': prepare_text_error(args),
            'icon_emoji': prepare_icon(args.icon_error)
        })

    return payload


def post_data(url, payload):
    # payload['text'] = json.dumps(payload)
    urlopen(url, data=json.dumps(payload))


def main(args):
    payload = prepare_data(args)
    post_data(args.webhook_url, payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('-c', '--channel',
                        default=os.environ.get('SLACK_CHANNEL', '#general'),
                        help='Can be a #channel or a direct message to a @username')

    parser.add_argument('-u', '--username',
                        default=os.environ.get('SLACK_USERNAME',
                                                platform.node() or 'a nice bot'),
                        help='The name of your bot')

    parser.add_argument('-i', '--icon-emoji',
                        default=os.environ.get('SLACK_ICON', 'smile'),
                        help='The icon of your bot')

    parser.add_argument('-t', '--text',
                        default=os.environ.get('SLACK_TEXT', 'it works!'),
                        help='The message to send')

    parser.add_argument('--icon-error',
                        default=os.environ.get('SLACK_ICON_ERROR', 'fearful'),
                        help='The icon to use in case of error')

    parser.add_argument('--text-error',
                        default=os.environ.get('SLACK_TEXT_ERROR'),
                        help='The message to send in case of error')

    parser.add_argument('--exit-status', type=int,
                        help='The flag to use to trigger an error message '
                             '(you can use the env variable `$?`)')

    parser.add_argument('webhook_url',
                        default=os.environ.get('SLACK_WEBHOOK_URL'))

    args = parser.parse_args()
    main(args)
