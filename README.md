# Generic User Interface

Python module to generate a CLI and GUI for user input validation.

This module provides a quick way to attach a user interface to arbitrary python scripts to promote them to readily usable tools. It takes care of the reoccurring task to prepare the user input for use with the actual procedure so you don't have to.

## Quickfacts

* Current Version: 0.1.1
* Python Version: 3.7.2
* Supported Platforms: PC
* Languages: English

## Usage Instructions

An example of how to use the module is given in the 'genui.py' file but also shown here to illustrate the simple integration:

```python
import os
from genui import GenericUI, Parameter

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
```

## Third Party

Used for the CLI is a package part of Python's built-ins:

* __argparse__: Parser for command-line options, arguments and sub-commands (https://docs.python.org/3/library/argparse.html)

Used for the GUI is a package included in Python's Windows installer:

* __tkinter__: Standard Python interface to the Tk GUI toolkit (https://docs.python.org/3/library/tkinter.html)

## Release Notes

### Version 0.1

Initial release.
