class ParsedLine(object):
    def __init__(self):
        self.timestamp = None
        self.queue_id = None
        self.original = None
        self.type = None
        self.subtype = None
        self.status = None
        self.fields = {}
        self.receiver = None
        self.process = None
        self.reject = False

    def __repr__(self):
        if self.subtype:
            return '<ParsedLine {} {}>'.format(self.type, self.subtype)
        else:
            return '<ParsedLine {}>'.format(self.type)


class EmailMessage(object):
    def __init__(self):
        self.queue_id = None
        self.parent_id = None
        self.source = None
        self.message_from = None
        self.message_to = None
        self.message_date = None
        self.size = None
        self.log_lines = []
        self.delivered = False
        self.transit_time = None
        self.status = "Unknown"
        self.direction = None

    def __repr__(self):
        return '<Email {} from {} to {} ({}, {})>'.format(self.queue_id, self.message_from, self.message_to,
                                                          self.direction, self.status)
