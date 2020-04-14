#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Module to apply a generic CLI and GUI to plain python scripts.

Using this module as shown at the bottom of this file you can add generic user interfaces.
The CLI complies to the Unix standard and the GUI provides the basic elements for user input,
argument validation and output to a separate window.

The decision whether to load the CLI or GUI is based on invocation through a terminal or the Explorer,
but can be overridden with a "--gui" parameter to load the GUI also from a terminal.
'''

import sys, os
import argparse
import psutil

from .gengui import GenericGUI, OrderedDict
from .parameter import Parameter

###############################################################################


class GenericUI:

    def __init__(self, parameters, main_function, title=None, version="1.0"):
        self.parameters = parameters
        self.main = main_function
        self.title = title
        self.version = version
        self.gui = None

    def run(self):
        # determine whether program was launched from explorer
        script = os.path.basename(sys.argv[0])
        if self.title is None:
            self.title = script

        exe = psutil.Process(os.getpid()).parent().name()
        parent_exe = psutil.Process(os.getpid()).parent().parent().name()

        load_ui = False
        if script == exe and parent_exe == 'explorer.exe':
            load_ui = True
        if '--gui' in sys.argv:
            sys.argv.remove('--gui')
            load_ui = True

        if load_ui:
            self.load_gui()
        else:
            self.load_cli()

    def load_cli(self):
        # prepare parameters for argparse
        parser = argparse.ArgumentParser()
        for parameter in self.parameters:
            identifiers = []
            specifiers = {}

            if not parameter.short and not parameter.long:
                identifiers.append(parameter.name)
            else:
                if parameter.short is not None:
                    identifiers.append(parameter.short)
                if parameter.long is not None:
                    identifiers.append(parameter.long)
                specifiers['dest'] = parameter.name

            if parameter.nargs != 1:
                if parameter.nargs == 0:
                    specifiers['action'] = 'store_true' if not parameter.default else 'store_false'
                else:
                    specifiers['nargs'] = parameter.nargs

            if parameter.default is not None:
                specifiers['default'] = parameter.default
            if parameter.meta is not None:
                specifiers['metavar'] = parameter.meta
            if parameter.help is not None:
                specifiers['help'] = parameter.help

            if 'action' not in specifiers:
                # convert any exception of parameter.verify to the argparse exception
                verify_func = parameter.verify
                if type(verify_func).__name__ != 'type':
                    def error_wrap(func):
                        def wrapped(value):
                            try:
                                return func(value)
                            except Exception as e:
                                raise argparse.ArgumentTypeError(str(e))
                        return wrapped
                    verify_func = error_wrap(verify_func)
                specifiers['type'] = verify_func

            parser.add_argument(*identifiers, **specifiers)
        args = parser.parse_args()

        # pass the arguments in a dictionary
        self.main(**vars(args))

    def load_gui(self):
        # prepare parameters for BasicGUI
        for parameter in self.parameters:
            verify_func = parameter.verify

            if type(verify_func).__name__ == 'type':
                # convert a type in verify_func to a type check
                def type_check(type_name):
                    def wrapped(value):
                        if type(value).__name__ != type_name:
                            raise ValueError('%s is not of type %s' % (value, type_name))
                        return value
                    return wrapped
                verify_func = type_check(verify_func.__name__)

            if parameter.nargs not in [0, 1, '?']:
                # with a list of arguments for a parameter convert verify_func
                # to do the validation for every list item
                def list_wrap(func):
                    def wrapped(values):
                        checked_list = []
                        for value in [value.strip() for value in values.split(',')]:
                            checked_list.append(func(value))
                        return checked_list
                    return wrapped
                verify_func = list_wrap(verify_func)

            parameter.verify = verify_func

        parameters = OrderedDict()
        parameters[self.version] = self.parameters
        self.gui = GenericGUI(self.title, parameters)

        # loop to allow re-run of the process with altered arguments
        while True:
            self.gui.get_input()
            if self.gui.should_quit:
                break

            # pass the arguments in a dictionary
            args = {}
            for parameter in parameters[self.gui.mode.get()]:
                args[parameter.name] = parameter.value

            self.main(**args)

        self.gui.join()


# implementation example ######################################################


def example_main(file_path, option):
    print('arguments:', file_path, option)

    # start working with the already validated arguments


if __name__ == "__main__":

    # define the functions for validation
    def is_file(value):
        if not os.path.isfile(value):
            error_msg = "%r is no file" % value
            raise ValueError(error_msg)
        return os.path.abspath(value)

    # list the required and optional input parameters
    parameters = [
        Parameter(name='file_path', meta='input file', nargs=1, verify=is_file,
                  help='path to the input file', widget='file'),
        Parameter(name='option', short='o', long='option', nargs=0, default=False,
                  help='an option that can left out to be set to False')
    ]

    # hand the "parameters" to the ui class as well as the function to call when all input is validated
    # that function has to have parameters identical to the names given the "parameters" list
    interface = GenericUI(parameters, example_main, "Example Tool", 1)
    interface.run()
