# Introduction

`slack-post.py` is your Slack Swiss Army Knife. It works using [Incoming Webhooks](https://api.slack.com/incoming-webhooks) and it's written in Python 3 using the Python Standard Library, so **no need to install dependencies**, you can just download the script and run it.

The script is able to:
 - post text;
 - post from a file;
 - post from `stdin`, so you can pipe it with other commands;
 - post the result of the execution of a command, capturing the `stdout`, `stderr`, execution time and exit code.

Posting the result of a command is super handy when you run non interactive scripts (e.g. stuff you put in a `crontab`) and you want to know the outcome of the execution.


# One-minute setup

1. Create a new [Incoming Webhook](https://my.slack.com/services/new/incoming-webhook/) (Slack will ask you to choose a channel where to post your messages, get a random one, it's not important)

2. Download the script `$ wget https://raw.githubusercontent.com/vrde/slack-utils/master/slack-post.py`

3. Make it executable `$ chmod +x slack-post.py`

3. Run the script `$ ./slack-post.py --webhook-url=<your-webhook-url> --channel=<the-target-channel>`

# Command Line Interface

```
  % ./slack-post.py -h
usage: slack-post.py [-h] [-c CHANNEL] [-u USERNAME] [-i ICON_EMOJI] [-t TEXT]
                     [-w WEBHOOK_URL] [-f FILE]
                     [command]

positional arguments:
  command               The command to execute

optional arguments:
  -h, --help            show this help message and exit
  -c CHANNEL, --channel CHANNEL
                        Can be a (#)channel or a direct message to a @username
                        (default: $SLACK_CHANNEL or #general)
  -u USERNAME, --username USERNAME
                        The name of your bot (default: $SLACK_USERNAME,
                        hostname)
  -i ICON_EMOJI, --icon-emoji ICON_EMOJI
                        The icon of your bot (default: $SLACK_ICON or
                        ":robot_face:")
  -t TEXT, --text TEXT  The message to send (default: $SLACK_TEXT or something
                        different)
  -w WEBHOOK_URL, --webhook-url WEBHOOK_URL
                        The URL to use to post the message (default:
                        $SLACK_WEBHOOK_URL
  -f FILE, --file FILE  Send the content of the specified file. Use - for
                        stdin.
```

Note that most of the arguments, if not defined, will fall back to their relative environment variable.

Pro tip: install `fortune` in the same machine where the script runs for major fun.


# Examples

All the examples make use of the `$SLACK_WEBHOOK_URL` variable. Set it now:
```bash
$ SLACK_WEBHOOK_URL=<your-webhook-url>
```

## Post a simple message
Let all the users `#general` know that you are cool because your computer can talk:
```bash
$ ./slack-post.py -t "My computer can talk"
```

![Simple post](http://i.imgur.com/HVGwQwd.png)


## Post the result of a command
This is a more interesting use case. `slack-post.py` will execute the command and post the result as a rich attachment to your Slack channel (here we are using the channel `#dev`)

```bash
$ ./slack-post.py -c dev df
```

If you need to add parameters to the command, you can use the double dash notation as in many other commands.
```bash
$ ./slack-post.py -c dev -- df -h
```

![Post with attachment](http://i.imgur.com/SQY28Qa.png)
