import re
from maildebug.guesstimate import find_mail_log


def log_line_regex(regex):
    files = find_mail_log()
    regex = re.compile(regex)
    result = []
    for file in files:
        if file.endswith('.gz'):
            continue
        with open(file) as handle:
            for line in handle.readlines():
                if regex.search(line):
                    result.append(line)
    return result


def trace(mail_id):
    loglines = log_line_regex(mail_id)
    for line in loglines:
        print(line)
