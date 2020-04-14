#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Generic graphical user interface for input parameters and output log as plug-in to any python program.

It spawns a thread that blocks the main application until the user entered the required parameters
and logs all output of the application to a separate window during execution.

usage:
    - specify the parameters you need from the user in an OrderedDict() with lists of Parameter objects
        parameters = OrderedDict()
        parameters[mode] = [Parameter(name1, type1), Parameter(name2, type2)]
        ui = BasicUI(title, parameters)
    - different modes are switchable by the user, but only one can be launched
    - parameter types supported are 'dir', 'file', 'text', 'pass', 'box'
    - to retrieve the parameters just read the parameters[ui.mode.get()][number].value.get()
    - all print and logging messages are redirected to the ui log window
    - use set_progress(percentage) to track progress in the progress bar
'''

import sys
import threading

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

from collections import OrderedDict

from .tktooltip import ToolTip
from .parameter import Parameter

###############################################################################


class GenericGUI(threading.Thread):

    mode = None
    input_frames = {}
    entries = {}
    help_text = {'dir': "Pick a directory...",
                 'file': "Pick a file...",
                 'fileordir': "Pick a file or directory...",
                 'text': "Enter...",
                 'pass': "",
                 'box': False}
    should_quit = False

    root_window = None
    log_window = None

    def __init__(self, title, parameters):
        self.title = title
        self.parameters = parameters
        self.event = threading.Event()

        threading.Thread.__init__(self)
        self.start()

    def get_input(self):
        self.event.clear()
        self.event.wait()

    def on_quit(self):
        self.should_quit = True
        self.root_window.quit()
        self.event.set()

    def on_log_quit(self):
        self.log_window.destroy()
        self.log_window = None
        self.set_disabled(self.root_window, False)

    def run(self):
        self.root_window = tk.Tk()

        self.mode = tk.StringVar()

        self.init_ui()
        if self.should_quit:
            return

        self.root_window.title(self.title)
        self.root_window.resizable(width=False, height=False)
        self.root_window.protocol('WM_DELETE_WINDOW', self.on_quit)
        self.root_window.bind('<Escape>', self.on_quit)

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout.write = self.log
        sys.stderr.write = self.log

        self.root_window.mainloop()

        sys.stdout = old_stdout
        sys.stderr = old_stderr

    def init_ui(self):
        self.style = ttk.Style()
        self.style.configure("Custom.TFrame", background='white')
        self.style.configure("Custom.TLabel", background='white')
        self.style.configure("Custom.TEntry", foreground='red', relief=tk.GROOVE)
        self.style.configure("Custom.TCheckbutton", background='white')
        self.style.configure("Log.TLabel", background='white', relief=tk.GROOVE)

        frame = ttk.Frame(self.root_window)
        frame.pack(fill=tk.BOTH, expand=True)

        # layout
        container = ttk.Frame(frame, style="Custom.TFrame")
        container.pack(fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # stack frames for different modes with the first being on top
        for key, values in reversed(list(self.parameters.items())):
            self.input_frames[key] = ttk.Frame(container, style="Custom.TFrame")
            self.input_frames[key].grid(row=0, column=0, sticky="nsew")
            self.row_count = 0
            for param in values:
                self.create_widget(key, param)

        launch_button = ttk.Button(frame, text="Run", command=self.confirm)
        launch_button.bind('<Return>', lambda event: self.confirm())
        launch_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # provide an option in case of multiple modes
        if len(self.parameters.keys()) > 1:
            drop_menu = ttk.OptionMenu(frame, self.mode, list(self.parameters.keys())[0], *self.parameters.keys(), command=self.change_frame)
            drop_menu.pack(side=tk.RIGHT, padx=5, pady=5)
        else:
            self.mode.set(list(self.parameters.keys())[0])
            label = ttk.Label(frame, text=self.mode.get())
            label.pack(side=tk.RIGHT, padx=5, pady=5)

    def create_widget(self, key, param):
        frame = self.input_frames[key]
        label = ttk.Label(frame, text=param.name + ':', style="Custom.TLabel")
        label.grid(row=self.row_count, column=0, padx=5, pady=5, sticky=tk.E)
        ToolTip(label, param.help)
        defaultValue = param.value

        # hacked checkboxes
        if param.widget == 'box':
            toggle = tk.BooleanVar()
            self.entries.setdefault(key, []).append(ttk.Checkbutton(frame, style="Custom.TCheckbutton", onvalue=True, offvalue=False, takefocus=False, variable=toggle))
            self.entries[key][-1].grid(row=self.row_count, column=1, padx=5, pady=5, sticky=tk.W)
            self.entries[key][-1].var = toggle
            self.entries[key][-1].var.set(self.help_text['box'])
            self.row_count += 1
            return

        self.entries.setdefault(key, []).append(ttk.Entry(frame))
        entry = self.entries[key][-1]
        entry.grid(row=self.row_count, column=1, padx=5, pady=5)
        entry.bind('<Button-1>', lambda event: self.handle_click(entry))

        if param.widget == 'dir':
            button = ttk.Button(frame, text="Browse...", command=lambda: self.ask_directory(entry))
            button.bind('<Return>', lambda event: self.ask_directory(entry))
            button.grid(row=self.row_count, column=2, padx=5, pady=5)
            self.set_entry(entry, self.help_text['dir'])
            #param.add_verification(lambda v: os.path.isdir(str(v)))
        elif param.widget == 'file':
            button = ttk.Button(frame, text="Browse...", command=lambda: self.ask_file(entry))
            button.bind('<Return>', lambda event: self.ask_file(entry))
            button.grid(row=self.row_count, column=2, padx=5, pady=5)
            self.set_entry(entry, self.help_text['file'])
            #param.add_verification(lambda v: os.path.isfile(str(v)))
        elif param.widget == 'fileordir':
            button_frame = ttk.Frame(frame, style="Custom.TFrame")
            button_frame.grid(row=self.row_count, column=2, padx=5, pady=5)
            button_file = ttk.Button(button_frame, text="File...", command=lambda: self.ask_file(entry), width=5)
            button_file.bind('<Return>', lambda event: self.ask_file(entry))
            button_file.grid(row=0, column=0, padx=0, pady=0)
            button_dir = ttk.Button(button_frame, text="Dir...", command=lambda: self.ask_directory(entry), width=5)
            button_dir.bind('<Return>', lambda event: self.ask_file(entry))
            button_dir.grid(row=0, column=1, padx=0, pady=0)
            self.set_entry(entry, self.help_text['fileordir'])
            #param.add_verification(lambda v: os.path.isfile(str(v)))
        elif param.widget == 'text':
            self.set_entry(entry, defaultValue or self.help_text['text'])
            #param.add_verification(lambda v: str(v) != "")
        elif param.widget == 'pass':
            self.entries[key][-1].config(show='*')
            self.set_entry(entry, self.help_text['pass'])
            #param.add_verification(lambda v: str(v) != "")
        else:
            print("ERROR: Only viable parameter types are 'file', 'dir', 'text', 'pass' and 'box'.")
            self.should_quit = True

        self.row_count += 1

    def set_entry(self, entry, text):
        entry.delete(0, tk.END)
        entry.insert(0, text)

    def handle_click(self, entry):
        if entry.get() in self.help_text.values():
            entry.delete(0, tk.END)

    def ask_directory(self, entry):
        dir_name = filedialog.askdirectory()
        if dir_name != "":
            self.set_entry(entry, dir_name)
        return

    def ask_file(self, entry):
        file_name = filedialog.askopenfilename()
        if file_name != "":
            self.set_entry(entry, file_name)
        return

    def change_frame(self, mode):
        if mode in self.input_frames.keys():
            self.input_frames[mode].tkraise()

    def confirm(self):
        completed = True
        for i, param in enumerate(self.parameters[self.mode.get()]):
            entry = self.entries[self.mode.get()][i]

            if param.widget == 'box':
                param.value = entry.var.get()
                continue

            try:
                value = param.verify(entry.get())
                if value != self.help_text[param.widget]:
                    entry.config(style="TEntry")
                    ToolTip(entry, False)
                    param.value = value
            except Exception as e:
                entry.config(style="Custom.TEntry")
                ToolTip(entry, str(e))
                completed = False

        print('completed', completed)
        if completed:
            self.set_disabled(self.root_window, True)
            self.create_log_window()
            self.event.set()

    def set_disabled(self, widget, bool):
        state = 'disable' if bool else 'normal'
        self.set_states(widget, state)

    def set_states(self, widget, mode):
        try:
            widget.configure(state=mode)
        except (AttributeError, tk.TclError):
            pass
        for child in widget.winfo_children():
            self.set_states(child, mode)

    def create_log_window(self):
        self.log_window = tk.Toplevel(self.root_window)
        self.log_window.minsize(width=400, height=200)
        self.log_window.geometry('800x600')
        self.log_window.wm_title("output log")
        self.log_window.configure(background='white')
        self.log_window.protocol('WM_DELETE_WINDOW', self.on_log_quit)

        self.log_list = tk.Listbox(self.log_window, relief=tk.FLAT, font=('Consolas', '9'), borderwidth=0, highlightthickness=0)
        self.log_list.pack(side=tk.LEFT, fill=tk.BOTH, padx=(5, 0), expand=True)
        self.log_scrollbar = ttk.Scrollbar(self.log_window, orient=tk.VERTICAL)
        self.log_scrollbar.config(command=self.log_list.yview)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_list.config(yscrollcommand=self.log_scrollbar.set)

        self.progress = tk.IntVar()
        self.progress_bar = ttk.Progressbar(self.log_list, orient=tk.HORIZONTAL, length=100, mode='determinate', variable=self.progress)
        self.progress_bar.place(relx=1.0, rely=1.0, x=-self.progress_bar.winfo_width(), y=-self.progress_bar.winfo_height(), anchor='se')
        self.progress_bar.place_forget()

    processing = False

    def set_progress(self, percentage):
        clamped_percentage = max(0, min(percentage, 100))
        if not self.processing and clamped_percentage > 0:
            self.progress_bar.place(relx=1.0, rely=1.0, x=-self.progress_bar.winfo_width(), y=-self.progress_bar.winfo_height(), anchor='se')
            self.processing = True
        elif self.processing and clamped_percentage == 100:
            self.progress_bar.place_forget()
            self.processing = False
        self.progress.set(clamped_percentage)

    msg_buffer = ""
    carriage_return = False

    def log(self, msg):
        if msg not in ['\n', '\r']:
            self.msg_buffer += msg
        else:
            try:
                if self.carriage_return:
                    self.log_list.delete(self.log_list.size() - 1)
                if msg == '\r':
                    self.carriage_return = True
                else:
                    self.carriage_return = False
                self.log_list.insert(tk.END, self.msg_buffer)
                self.log_list.yview(tk.END)
            except Exception as e:
                pass
            finally:
                self.msg_buffer = ""

    def catch_subprocess_output(self, process_handle):
        while True:
            nextline = process_handle.stdout.read(1).decode(sys.stdout.encoding, errors='replace')
            if nextline == '' and process_handle.poll() is not None:
                break
            print(nextline, end='')


# implementation example ######################################################

def example_main():
    # example for application output
    for i in range(20):
        import time
        time.sleep(0.5)
        print("message #%d " % i + "lo" + 'o' * i + "ng")


if __name__ == '__main__':
    parameters = OrderedDict()
    parameters["mode 1"] = [Parameter("working dir", 'dir'),
                            Parameter("file_name", 'file'),
                            Parameter("option", 'text')]
    parameters["mode 2"] = [Parameter("username", 'text', lambda v: str(v) != "user"),
                            Parameter("password", 'pass'),
                            Parameter("option", 'box')]
    ui = GenericGUI("Test App", parameters)

    while True:
        ui.get_input()
        if ui.should_quit:
            break

        mode = ui.mode.get()
        del sys.argv[1:]
        for param in parameters[ui.mode.get()]:
            print(param.name, param.value.get())
            sys.argv.append(param.value.get())

        example_main()

    ui.join()
