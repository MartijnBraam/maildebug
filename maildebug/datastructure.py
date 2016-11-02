class ParsedLine(object):
    def __init__(self):
        self.original = None
        self.type = None
        self.subtype = None
        self.status = None
        self.fields = {}
        self.receiver = None

    def __repr__(self):
        if self.subtype:
            return '<ParsedLine {} {}>'.format(self.type, self.subtype)
        else:
            return '<ParsedLine {}>'.format(self.type)
