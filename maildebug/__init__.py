import argparse
from arghandler import *
import maildebug.tracer
import maildebug.guesstimate


@subcmd
def trace(parser, context, args):
    parser.add_argument('mail_id')
    args = parser.parse_args(args)
    maildebug.tracer.trace(args.mail_id)


@subcmd
def guesses(parser, context, args):
    print("--[ Mail log files ]--")
    for log in maildebug.guesstimate.find_mail_log():
        print(log)


if __name__ == '__main__':
    handler = ArgumentHandler(description='Mail debugger')
    handler.run()
