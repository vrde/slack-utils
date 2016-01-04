#!/usr/bin/env python
'''Post a message to Slack.

Useful when you run commands automatically, e.g. in a crontab, and you need
a feedback from the execution.

The script can run in three modes:
 1. simple mode, posting a message to a channel;
 2. exit status mode, posting a message and the exit status (that you need to
    provide using the `--exit-status` to the script) to a channel;
 3. command mode, posting a message, the status code, stderr and stdout, and
    the execution time of a command to a channel.

The script uses "Incoming Webhooks" by Slack, you can find more info about
some of the params here:
 - https://api.slack.com/incoming-webhooks

'''

import argparse
import json
import os
import subprocess
import platform
import sys
from datetime import datetime
from tempfile import NamedTemporaryFile
from urllib2 import urlopen


def prepare_text_error(args):
    if args.text_error:
        return args.text_error

    return u'FAILURE: {}'.format(args.text)


def read_and_truncate(f, size=1024, relax=10, encoding='UTF-8'):
    f.seek(0)
    filesize = os.path.getsize(f.name)

    if filesize < size * (1 + relax / 100.):
        size = filesize

    data = f.read(size)
    data = data.decode(encoding)

    if filesize > size:
        data = u'\n'.join([data, u'[...{} bytes truncated]'.format(filesize - size)])

    return data


def execute_command(command):
    stdout = NamedTemporaryFile()
    stderr = NamedTemporaryFile()

    start = datetime.now()
    proc = subprocess.Popen(command, stdout=stdout, stderr=stderr, shell=True)
    proc.communicate()
    delta = datetime.now() - start

    stdout_data = read_and_truncate(stdout, encoding=sys.stdout.encoding)
    stderr_data = read_and_truncate(stderr, encoding=sys.stderr.encoding)

    stdout.close()
    stderr.close()

    return proc.returncode, stdout_data, stderr_data, delta

def prepare_data(args):
    exit_status = args.exit_status
    text = args.text

    if args.command:
        exit_status, stdout, stderr, delta = execute_command(args.command)
        text = [u'command: `{}`'.format(u' '.join(args.command))]
        text.append('execution time: {}'.format(delta))

        if exit_status != 0:
            text.append(u'exit code: {}'.format(exit_status))
        if stdout:
            text.append('')
            text.append('```{}```'.format(stdout))
        if stderr:
            text.append('')
            text.append('```{}```'.format(stderr))

        text = u'\n'.join(text)

    payload = {
        'channel': args.channel,
        'username': args.username,
        'text': text,
        'icon_emoji': args.icon_emoji
    }

    if exit_status is not None and exit_status != 0:
        payload.update({
            'icon_emoji': args.icon_error
        })

    return payload


def post_data(url, payload):
    urlopen(url, data=json.dumps(payload))


def main(args):
    payload = prepare_data(args)
    post_data(args.webhook_url, payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
                                     # formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-c', '--channel',
                        default=os.environ.get('SLACK_CHANNEL', '#general'),
                        help='Can be a #channel or a direct message to a @username '
                             '(default: $SLACK_CHANNEL or #general)')

    parser.add_argument('-u', '--username',
                        default=os.environ.get('SLACK_USERNAME',
                                                platform.node() or 'a nice bot'),
                        help='The name of your bot '
                             '(default: $SLACK_USERNAME, hostname or "a nice bot")')

    parser.add_argument('-i', '--icon-emoji',
                        default=os.environ.get('SLACK_ICON', ':smile:'),
                        help='The icon of your bot '
                             '(default: $SLACK_ICON or ":smile:")')

    parser.add_argument('-t', '--text',
                        default=os.environ.get('SLACK_TEXT', 'it works!'),
                        help='The message to send '
                             '(default: $SLACK_TEXT or "it works!")')

    parser.add_argument('--icon-error',
                        default=os.environ.get('SLACK_ICON_ERROR', ':fearful:'),
                        help='The icon to use in case of error '
                             '(default: $SLACK_ICON_ERROR or ":fearful:")')

    parser.add_argument('--text-error',
                        default=os.environ.get('SLACK_TEXT_ERROR'),
                        help='The message to send in case of error '
                             '(default: $SLACK_ICON_ERROR or ":fearful:")')

    parser.add_argument('--exit-status',
                        type=int,
                        help='The flag to use to trigger an error message '
                             '(you can use the env variable `$?`)')

    parser.add_argument('webhook_url',
                        default=os.environ.get('SLACK_WEBHOOK_URL'),
                        help='The URL to use to post the message'
                             '(default: $SLACK_WEBHOOK_URL')

    parser.add_argument('command',
                        nargs='?',
                        help='The command to execute') 

    args, extra = parser.parse_known_args()
    if args.command:
        args.command = [args.command] + extra
    main(args)
