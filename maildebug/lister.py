from maildebug.datastructure import EmailMessage
from maildebug.explain import explain_line
from maildebug.guesstimate import find_mail_log
import ipaddress


def list_traffic(send_to=None, send_from=None, day=None, delivered=None, direction=None):
    if send_to or send_from or day or delivered is not None or direction is not None:
        print('--[ Filters ]--')
        if send_to:
            print('To: {}'.format(send_to))
        if send_from:
            print('From: {}'.format(send_from))
        if day:
            print('Day: {:%Y-%m-%d}'.format(day))
        if delivered is not None:
            if delivered:
                print('Delivery: successful')
            else:
                print('Delivery: failed')
        if direction is not None:
            print('Direction: {}'.format(direction))
        print()

        iterator = MessageIterator()
        for message in iterator.iterate_logs():
            print(message)


class MessageIterator:
    def __init__(self):
        self.traces = {}
        self.processes = {}
        self.lda = {}

    def iterate_logs(self):
        files = find_mail_log()
        for file in files:
            if file.endswith('.gz'):
                # TODO: Decompress and search
                continue
            with open(file) as handle:
                for line in handle:
                    explanation = explain_line(line)
                    if explanation.process:
                        if explanation.process not in self.processes.keys():
                            self.processes[explanation.process] = [explanation]
                        else:
                            self.processes[explanation.process].append(explanation)
                            if explanation.subtype == 'disconnect':
                                del self.processes[explanation.process]
                            if explanation.reject:
                                yield self.aggregate_reject(self.processes[explanation.process])
                                del self.processes[explanation.process]
                                continue

                    if explanation.queue_id:
                        if explanation.queue_id not in self.traces.keys():
                            if explanation.process and explanation.process in self.processes.keys():
                                self.traces[explanation.queue_id] = self.processes[explanation.process][:]
                            else:
                                self.traces[explanation.queue_id] = [explanation]
                        else:
                            self.traces[explanation.queue_id].append(explanation)
                        if explanation.type == 'delivery' and explanation.subtype == 'lda':
                            self.lda[explanation.queue_id] = {
                                'message-id': self.get_line_type(explanation.queue_id, 'cleanup').fields['message-id']
                            }

                        if explanation.type == 'complete' and explanation.queue_id not in self.lda:
                            yield self.aggregate_info(explanation.queue_id)
                            del self.traces[explanation.queue_id]

                    else:
                        if explanation.subtype == 'lda':
                            message_id = explanation.fields['message-id']
                            for lda_queue_id in list(self.lda):
                                if self.lda[lda_queue_id]['message-id'] == message_id:
                                    self.traces[lda_queue_id].append(explanation)
                                    yield self.aggregate_info(lda_queue_id, lda=True)
                                    del self.traces[lda_queue_id]
                                    del self.lda[lda_queue_id]
                                    continue

    def aggregate_info(self, queue_id, lda=False):
        message = EmailMessage()
        message.queue_id = queue_id
        message.log_lines = self.traces[queue_id][:]

        envelope = self.get_line_type(queue_id, 'message')
        message.message_from = envelope.fields['from']
        message.size = envelope.fields['size']

        message.message_date = message.log_lines[0].timestamp
        message.transit_time = message.log_lines[-1].timestamp - message.log_lines[0].timestamp

        local_drop = False

        drop = message.log_lines[0]
        drop_ip = ipaddress.ip_address(drop.fields['ip'])
        if isinstance(drop_ip, ipaddress.IPv4Address) and (drop_ip.is_private or drop_ip.is_link_local):
            local_drop = True
        if isinstance(drop_ip, ipaddress.IPv6Address) and drop_ip.is_site_local:
            local_drop = True

        directions = {
            (False, False): "Transport",
            (True, False): "Outbound",
            (False, True): "Inbound",
            (True, True): "Internal"
        }

        message.direction = directions[(local_drop, lda)]

        if lda:
            delivery = message.log_lines[-1]
            message.message_to = delivery.fields['mailbox']
            message.delivered = True
            message.status = "Delivered"
        else:
            delivery = self.get_line_type(queue_id, 'delivery')
            message.message_to = delivery.receiver

            if delivery.fields['dsn'][0] == '2':
                message.delivered = True
                message.status = "Relayed"

        return message

    def aggregate_reject(self, log_lines):
        message = EmailMessage()
        message.log_lines = log_lines
        message.message_date = message.log_lines[0].timestamp
        message.delivered = False
        message.status = "Rejected on entry"
        return message

    def get_line_type(self, queue_id, line_type):
        for line in self.traces[queue_id]:
            if line.type == line_type:
                return line
