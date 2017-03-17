import re
import textwrap
import humanize
from colored import fg, attr
import datetime

from maildebug.datastructure import ParsedLine

REGEX_POSTFIX_PICKUP = re.compile(r'postfix/pickup\[\d+\]: ([^:]+): (.+)')
REGEX_POSTFIX_SUBMISSION = re.compile(r'postfix/submission/smtpd\[\d+\]: ([^:]+): (.+)')
REGEX_POSTFIX_CLEANUP = re.compile(r'postfix/cleanup\[\d+\]: ([^:]+): (.+)')
REGEX_POSTFIX_QMGR = re.compile(r'postfix/qmgr\[\d+\]: ([^:]+): (.+)')
REGEX_POSTFIX_QMGR_FROM = re.compile(r'postfix/qmgr\[\d+\]: ([^:]+): from=(.+)')
REGEX_POSTFIX_QMGR_REMOVED = re.compile(r'postfix/qmgr\[\d+\]: ([^:]+): removed')
REGEX_POSTFIX_SMTP = re.compile(r'postfix/(?:smtp|pipe)\[\d+\]: ([^:]+): (.+)')
REGEX_POSTFIX_SMTP_TO = re.compile(r'postfix/(?:smtp|pipe)\[\d+\]: ([^:]+): to=(.+)')
REGEX_POSTFIX_SMTPD_CONNECT = re.compile(r'postfix/smtpd\[(\d+)\]: connect from ([^\[]+)\[([^\]]+)\]')
REGEX_POSTFIX_SMTPD_QUEUE = re.compile(r'postfix/smtpd\[(\d+)\]: ([^:]+): client=(.+)')
REGEX_POSTFIX_SMTPD_NOQUEUE = re.compile(r'postfix/smtpd\[(\d+)\]: NOQUEUE: reject: RCPT from [^ ]+ (.+)')
REGEX_POSTFIX_SMTPD_DISCONNECT = re.compile(r'postfix/smtpd\[(\d+)\]: disconnect from ([^\[]+)\[([^\]]+)\]')
REGEX_OPENDKIM = re.compile(r'opendkim\[\d+\]: ([^:]+): (.+)')
REGEX_AMAVIS_PASS = re.compile(
    r'amavis\[\d+\]: \([^\)]+\) Passed CLEAN \{([^\}]+)\}, [^ ]+ [^ ]+ [^ ]+ -> [^,]+, Queue-ID: ([^,]+)')
REGEX_DOVECOT_LDA_SIEVE = re.compile(r'dovecot: lda\(([^\)]+)\): sieve: msgid=([^:]+): (.+)')

REGEX_TIMESTAMP = re.compile(r'^[a-zA-Z]{3} \d{2} \d{2}:\d{2}:\d{2}')

REGEX_SUCCESS_DSN = re.compile(r'2\.\d+\.\d+')


def explain_line(line):
    if REGEX_POSTFIX_SMTPD_CONNECT.search(line):
        return add_timestamp(explain_postfix_smtpd_connect(line))
    if REGEX_POSTFIX_SMTPD_DISCONNECT.search(line):
        return add_timestamp(explain_postfix_smtpd_disconnect(line))
    if REGEX_POSTFIX_SMTPD_QUEUE.search(line):
        return add_timestamp(explain_postfix_smtpd_queue(line))
    if REGEX_POSTFIX_SMTPD_NOQUEUE.search(line):
        return add_timestamp(explain_postfix_smtpd_noqueue(line))
    if REGEX_OPENDKIM.search(line):
        return add_timestamp(explain_opendkim(line))
    if REGEX_POSTFIX_PICKUP.search(line):
        return add_timestamp(explain_postfix_pickup(line))
    if REGEX_POSTFIX_SUBMISSION.search(line):
        return add_timestamp(explain_postfix_submission(line))
    if REGEX_POSTFIX_CLEANUP.search(line):
        return add_timestamp(explain_postfix_cleanup(line))
    if REGEX_POSTFIX_QMGR_FROM.search(line):
        return add_timestamp(explain_postfix_qmgr_from(line))
    if REGEX_POSTFIX_SMTP_TO.search(line):
        return add_timestamp(explain_postfix_smtp_to(line))
    if REGEX_AMAVIS_PASS.search(line):
        return add_timestamp(explain_amavis_pass(line))
    if REGEX_DOVECOT_LDA_SIEVE.search(line):
        return add_timestamp(explain_dovecot_lda_sieve(line))
    if REGEX_POSTFIX_QMGR_REMOVED.search(line):
        result = ParsedLine()
        result.original = line
        result.type = 'complete'
        part = REGEX_POSTFIX_QMGR_REMOVED.search(line)
        result.queue_id = part.group(1)
        return add_timestamp(result)

    result = ParsedLine()
    result.original = line
    result.type = 'unknown'
    return add_timestamp(result)


def add_timestamp(result):
    timestamp = REGEX_TIMESTAMP.search(result.original).group(0)
    timestamp += " " + str(datetime.datetime.now().year)
    result.timestamp = datetime.datetime.strptime(timestamp, '%b %d %H:%M:%S %Y')
    return result


def make_dict_color(input_dict, color):
    output_dict = {}
    for key in input_dict.keys():
        output_dict[key] = fg(color) + input_dict[key] + attr(0)
    return output_dict


def print_input_info(input_explanations):
    source = None
    message_id = None
    from_addr = None
    size = None

    for ex in input_explanations:
        if ex.type == 'pickup':
            source = ex
        if ex.type == 'cleanup':
            message_id = ex.fields['message-id']
        if ex.type == 'message':
            from_addr = ex.fields['from']
            size = ex.fields['size']

    if source.subtype == 'local':
        print(
            "Received message from local unix account {from} ({uid})".format(**make_dict_color(source.fields, 'blue')))
    elif source.subtype == 'remote-authenticated':
        print("Received message from {client} after logging in as {sasl_username}".format(
            **make_dict_color(source.fields, 'blue')))

    print("Message-id: {}".format(fg('blue') + message_id + attr(0)))
    print("From:       {}".format(fg('blue') + from_addr + attr(0)))
    print("Size:       {}".format(size))


def print_delivery_info(addr, delivery_explanations):
    by_dsn = {}
    for ex in delivery_explanations:
        dsn = ex.status
        if dsn not in by_dsn.keys():
            by_dsn[dsn] = []
        by_dsn[dsn].append(ex)

    ex = delivery_explanations[0]

    print("Deliver to {}:".format(fg('blue') + addr + attr(0)))
    success = False
    if ex.subtype == 'smtp':
        if len(delivery_explanations) == 1:
            if 'relay' in ex.fields.keys():
                print("\tRelay throug {}".format(ex.fields['relay']))
            if REGEX_SUCCESS_DSN.search(ex.fields['status']):
                success = True
            response = textwrap.indent(textwrap.fill(ex.fields['status']), '\t')
            print(response)
            if success:
                print(fg('green') + "\tDelivery successful" + attr(0))
            else:
                print(fg('red') + "\tNot delivered (yet)" + attr(0))
        else:
            for dsn in by_dsn.keys():
                dsn_colored = dsn
                if dsn[0] == '2':
                    dsn_colored = fg('green') + dsn + attr(0)
                    success = True
                elif dsn[0] == '4':
                    dsn_colored = fg('yellow') + dsn + attr(0)
                elif dsn[0] == '5':
                    dsn_colored = fg('red') + dsn + attr(0)
                print("\t{}x status {}".format(len(by_dsn[dsn]), dsn_colored))
                response = by_dsn[dsn][0].fields['status']
                response = textwrap.indent(textwrap.fill(response), '\t\t')
                print(response)
                if success:
                    print(fg('green') + "\tDelivery successful" + attr(0))
                else:
                    print(fg('red') + "\tNot delivered (yet)" + attr(0))


def explain_postfix_smtpd_connect(line):
    result = ParsedLine()
    result.original = line
    result.type = 'smtpd'
    result.subtype = 'connect'
    part = REGEX_POSTFIX_SMTPD_CONNECT.search(line)
    result.process = int(part.group(1))
    result.fields['hostname'] = part.group(2)
    result.fields['ip'] = part.group(3)
    return result


def explain_postfix_smtpd_disconnect(line):
    result = ParsedLine()
    result.original = line
    result.type = 'smtpd'
    result.subtype = 'disconnect'
    part = REGEX_POSTFIX_SMTPD_DISCONNECT.search(line)
    result.process = int(part.group(1))
    result.fields['hostname'] = part.group(2)
    result.fields['ip'] = part.group(3)
    return result


def explain_postfix_smtpd_queue(line):
    result = ParsedLine()
    result.original = line
    result.type = 'smtpd'
    result.subtype = 'queue'
    part = REGEX_POSTFIX_SMTPD_QUEUE.search(line)
    result.process = int(part.group(1))
    result.queue_id = part.group(2)
    return result


def explain_postfix_smtpd_noqueue(line):
    result = ParsedLine()
    result.original = line
    result.type = 'smtpd'
    result.subtype = 'noqueue'
    part = REGEX_POSTFIX_SMTPD_NOQUEUE.search(line)
    result.process = int(part.group(1))
    result.fields['message'] = part.group(2)
    result.reject = True
    return result


def explain_amavis_pass(line):
    result = ParsedLine()
    result.original = line
    result.type = 'amavis'
    result.subtype = 'pass'
    part = REGEX_AMAVIS_PASS.search(line)
    result.fields['type'] = part.group(1)
    result.queue_id = part.group(2)
    return result


def explain_dovecot_lda_sieve(line):
    result = ParsedLine()
    result.original = line
    result.type = 'dovecot'
    result.subtype = 'lda'
    part = REGEX_DOVECOT_LDA_SIEVE.search(line)
    result.fields['mailbox'] = part.group(1)
    result.fields['message-id'] = part.group(2)
    return result


def explain_opendkim(line):
    result = ParsedLine()
    result.original = line
    result.type = 'opendkim'
    part = REGEX_OPENDKIM.search(line)
    result.queue_id = part.group(1)
    result.fields['output'] = part.group(2)
    return result


def explain_postfix_pickup(line):
    result = ParsedLine()
    result.original = line
    result.type = 'pickup'
    result.subtype = 'local'
    part = REGEX_POSTFIX_PICKUP.search(line)
    result.queue_id = part.group(1)
    raw = part.group(2)
    field = raw.split(' ')
    fields = {}
    for f in field:
        name, value = f.split("=", 1)
        fields[name] = value
    result.fields = fields
    return result


def explain_postfix_submission(line):
    result = ParsedLine()
    result.original = line
    result.type = 'pickup'
    result.subtype = 'remote-authenticated'
    part = REGEX_POSTFIX_SUBMISSION.search(line)
    result.queue_id = part.group(1)
    raw = part.group(2)
    field = raw.split(', ')
    fields = {}
    for f in field:
        name, value = f.split("=", 1)
        fields[name] = value
    result.fields = fields
    return result


def explain_postfix_cleanup(line):
    result = ParsedLine()
    result.original = line
    result.type = 'cleanup'
    part = REGEX_POSTFIX_CLEANUP.search(line)
    result.queue_id = part.group(1)
    raw = part.group(2)
    field = raw.split(', ')
    fields = {}
    for f in field:
        name, value = f.split("=", 1)
        fields[name] = value
    result.fields = fields
    return result


def explain_postfix_qmgr_from(line):
    result = ParsedLine()
    result.original = line
    result.type = 'message'
    part = REGEX_POSTFIX_QMGR.search(line)
    result.queue_id = part.group(1)
    raw = part.group(2)
    field = raw.split(', ')
    fields = {}
    for f in field:
        name, value = f.split("=", 1)
        if name == "size":
            value = int(value)
            value = humanize.naturalsize(value)
        fields[name] = value
    result.fields = fields
    return result


def explain_postfix_smtp_to(line):
    result = ParsedLine()
    result.type = 'delivery'
    result.subtype = 'smtp'
    result.original = line
    if 'status=' in line:
        before, after = line.split('status=', 1)
        after = after.replace(', ', '. ')
        line = '{}status={}'.format(before, after)
    part = REGEX_POSTFIX_SMTP.search(line)
    result.queue_id = part.group(1)
    raw = part.group(2)
    field = raw.split(', ')
    fields = {}
    for f in field:
        name, value = f.split("=", 1)
        fields[name] = value
    result.fields = fields
    result.receiver = fields['to']
    result.status = fields['dsn']

    if 'relay' in result.fields:
        if '127.0.0.1' in result.fields['relay']:
            result.subtype = 'lda'
        if 'dovecot' in result.fields['relay']:
            result.subtype = 'lda'

    return result
