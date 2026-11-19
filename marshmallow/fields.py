"""Stub fields for marshmallow used in ClaimSightAI.
Only basic field classes are defined; they simply store the provided arguments.
"""

class Field:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class Str(Field):
    pass

class Email(Field):
    pass

class Int(Field):
    pass

class Date(Field):
    pass