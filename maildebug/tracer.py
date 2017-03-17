import re
from maildebug.guesstimate import find_mail_log
from maildebug.explain import explain_line, print_input_info, print_delivery_info
from colored import fg, bg, attr


def log_line_regex(regex):
    files = find_mail_log()
    regex = re.compile(regex)
    result = []
    for file in files:
        if file.endswith('.gz'):
            # TODO: Decompress and search
            continue
        with open(file) as handle:
            for line in handle.readlines():
                if regex.search(line):
                    result.append(line)
    return result


def trace(mail_id):
    loglines = log_line_regex(mail_id)
    input_part = []
    output_parts = {}
    had_output = False
    input_types = ['pickup', 'message', 'cleanup']
    for line in loglines:
        explanation = explain_line(line)
        if explanation.type not in input_types:
            had_output = True
        if not had_output or explanation.type in input_types:
            input_part.append(explanation)
        else:
            receiver = explanation.receiver
            if receiver:
                if receiver not in output_parts.keys():
                    output_parts[receiver] = []
                output_parts[receiver].append(explanation)

    print_input_info(input_part)
    for to_addr in output_parts.keys():
        print()
        print_delivery_info(to_addr, output_parts[to_addr])
