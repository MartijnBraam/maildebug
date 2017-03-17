import argparse
from arghandler import *
import maildebug.tracer
import maildebug.guesstimate
import maildebug.lister
from datetime import date, timedelta, datetime


@subcmd
def trace(parser, context, args):
    parser.add_argument('mail_id')
    args = parser.parse_args(args)
    maildebug.tracer.trace(args.mail_id)


@subcmd
def list(parser, context, args):
    parser.add_argument('--from', help='From address (regex)')
    parser.add_argument('--to', help='To address (regex)')

    parser.add_argument('--show-reject-on-entry', help="Show early rejections", action='store_true',
                        dest='early_reject')

    today = date.today().__format__('%Y-%m-%d')
    yesterday = (date.today() - timedelta(-1)).__format__('%Y-%m-%d')

    dategroup = parser.add_mutually_exclusive_group()
    dategroup.add_argument('--today', help='Show only from today', dest='day', action='store_const', const=today)
    dategroup.add_argument('--yesterday', help='Show only from yesterday', dest='day', action='store_const',
                           const=yesterday)
    dategroup.add_argument('--day', help='Filter to specific day (yyyy-mm-dd)', dest='day')

    deliverygroup = parser.add_mutually_exclusive_group()
    deliverygroup.add_argument('--delivered', help='Show only delivered messages', dest='delivered',
                               action='store_const', const=True)
    deliverygroup.add_argument('--undelivered', help='Show only undelivered messages', dest='delivered',
                               action='store_const', const=False)

    directiongroup = parser.add_mutually_exclusive_group()
    directiongroup.add_argument('--inbound', help='Show only incoming mail', dest='direction', action='store_const',
                                const='Inbound')
    directiongroup.add_argument('--outbound', help='Show only outgoing mail', dest='direction', action='store_const',
                                const='Outbound')
    directiongroup.add_argument('--internal', help='Show only internal mail', dest='direction', action='store_const',
                                const='Internal')
    directiongroup.add_argument('--transport', help='Show only transport mail', dest='direction', action='store_const',
                                const='Transport')

    args = parser.parse_args(args)

    day = None
    if args.day:
        day = datetime.strptime(args.day, '%Y-%m-%d')

    maildebug.lister.list_traffic(send_to=args.to, send_from=getattr(args, 'from'), day=day, delivered=args.delivered,
                                  direction=args.direction, early_reject=args.early_reject)


@subcmd
def guesses(parser, context, args):
    print("--[ Mail log files ]--")
    for log in maildebug.guesstimate.find_mail_log():
        print(log)


if __name__ == '__main__':
    handler = ArgumentHandler(description='Mail debugger')
    handler.run()
