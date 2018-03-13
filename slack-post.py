#!/usr/bin/env python3
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
import getpass
import json
import os
import platform
import subprocess
import sys

from datetime import datetime
from tempfile import NamedTemporaryFile
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


def e(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def read_and_truncate(f, size=1024, relax=10, encoding='UTF-8'):
    f.seek(0)
    filesize = os.path.getsize(f.name)

    if filesize < size * (1 + relax / 100.):
        size = filesize

    data = f.read(size)
    if encoding:
        data = data.decode(encoding)

    if filesize > size:
        data = '\n'.join([data, '[...{} bytes truncated]'.format(filesize - size)])

    return data


def get_random_text():
    try:
        return e(subprocess.check_output(['fortune']).decode(sys.stdout.encoding))
    except FileNotFoundError:
        return 'I love cats!'


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


def prepare_command(command):
    exit_code, stdout, stderr, delta = execute_command(command)

    plain_command = ' '.join(command)

    attachment = {
        'color': 'good',
        'fallback': None,
        # 'text': None,
        # 'pretext': None,
        'mrkdwn_in': ['pretext', 'text', 'fields'],
        'fields': [{
            'title': 'command',
            'value': e('`{}`'.format(plain_command)),
            'short': True
        }, {
            'title': 'execution time',
            'value': str(delta),
            'short': True
        }]
    }

    if exit_code != 0:
        attachment['color'] = 'danger'
        attachment['fallback'] = e('[exit code: {}] Failed to execute: {}'.format(exit_code, plain_command))
        attachment['fields'].append({
            'title': 'exit code',
            'value': exit_code,
            'short': True
        })
        attachment['fields'].append({
            'title': 'stderr',
            'value': e('```{}```'.format(stderr) if stderr else '_no output_')
        })
    else:
        attachment['fallback'] = e('Succeded to execute: {}'.format(plain_command))
        attachment['fields'].append({
            'title': 'stdout',
            'value': e('```{}```'.format(stdout) if stdout else '_no output_')
        })

    return attachment


def prepare_data(text=None, filename=None, channel=None, command=None,
                 username=None, icon_emoji=None):
    text = [text]

    if filename == '-':
        text.append('```{}```'.format(sys.stdin.read()))
    elif filename:
        with open(filename) as f:
            text.append('```{}```'.format(f.read()))

    channel = channel

    if channel[0] not in ('#', '@'):
        channel = '#{}'.format(channel)

    text = list(filter(bool, text))

    if not text and not command:
        text = [get_random_text()]

    payload = {
        'channel': channel,
        'username': username,
        'text': e('\n'.join(text)),
        'icon_emoji': icon_emoji,
    }

    if command:
        payload['attachments'] = [prepare_command(command)]

    return payload


def post_data(url, payload):
    urlopen(url, data=json.dumps(payload).encode('utf-8'))


def main(args):
    payload = prepare_data(args.text, args.file, args.channel,
                           args.command, args.username, args.icon_emoji)
    post_data(args.webhook_url, payload)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
                                     # formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-c', '--channel',
                        default=os.environ.get('SLACK_CHANNEL', '#general'),
                        help='Can be a (#)channel or a direct message to a @username '
                             '(default: $SLACK_CHANNEL or #general)')

    parser.add_argument('-u', '--username',
                        default=os.environ.get('SLACK_USERNAME',
                                                '{}@{}'.format(getpass.getuser(),
                                                                platform.node())),
                        help='The name of your bot (default: $SLACK_USERNAME, hostname)')

    parser.add_argument('-i', '--icon-emoji',
                        default=os.environ.get('SLACK_ICON', ':robot_face:'),
                        help='The icon of your bot (default: $SLACK_ICON or ":robot_face:")')

    parser.add_argument('-t', '--text',
                        default=os.environ.get('SLACK_TEXT'),
                        help='The message to send (default: $SLACK_TEXT or something different)')

    parser.add_argument('-w', '--webhook-url',
                        default=os.environ.get('SLACK_WEBHOOK_URL'),
                        help='The URL to use to post the message (default: $SLACK_WEBHOOK_URL')

    parser.add_argument('-f', '--file',
                        help='Post the content of a text file. Use - for stdin.')

    parser.add_argument('command',
                        nargs='?',
                        help='The command to execute')

    args, extra = parser.parse_known_args()
    if args.command:
        args.command = [args.command] + extra
    if not args.webhook_url:
        parser.error('Please either set the $SLACK_WEBHOOK_URL variable, or '
                     'provide a value for the -w parameter')
    main(args)
