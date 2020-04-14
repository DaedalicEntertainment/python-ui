#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Parameter class to be used by generic graphical and command line interface.

CONFIGURATION
    name: identifier for the use within python scripts
    short: short variant of the name used in command line as '-e'
    long: long variant of the name used in command line as '--example'
    meta: variant of the name used for description
    nargs: number of arguments, integer or '?' (for zero or one), '*' (for zero or more), '+' (for one or more)
    verify: function for validation of user input like the example below class definition
    help: text to describe the parameter displayed for help
    widget: widget type to be used for the gui
'''

from inspect import signature

###############################################################################


class Parameter:

    used_flags=set()

    def __init__(self, name, short=None, long=None, meta=None, nargs=1, default=None, verify=lambda value: value, help=None, widget='text'):
        self.name = name

        self.short = '-' + short if short is not None else None
        if self.short is not None:
            if self.short in Parameter.used_flags:
                raise ValueError("Short flag '%s' for parameter %s is already used" % (short, name))
            else:
                Parameter.used_flags.add(self.short)
        self.long = '--' + long if long is not None else None
        if self.long is not None:
            if self.long in Parameter.used_flags:
                raise ValueError("Long flag '%s' for parameter %s is already used" % (long, name))
            else:
                Parameter.used_flags.add(self.long)

        self.meta = meta or name if long != name else None
        self.nargs = nargs
        self.default = default
        self.value = default
        self.widget = widget if nargs != 0 else 'box'
        self.help = help

        if len(signature(verify).parameters) == 1:
            self.verify = verify
        else:
            raise ValueError("Function for verification of '%s' needs to have exactly 1 parameter." % self.name)


def example_verify(value):
    if value is None:
        error_msg = "%s is None" % value
        raise ValueError(error_msg)
    return value
