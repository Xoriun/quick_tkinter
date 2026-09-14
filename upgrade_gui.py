"""
Copyright 2018 - 2024 <PySimpleGUI>
          2024 - 2026 <Xoriun>
"""

import json
import os
import platform
import re
import socket
import sys
import tempfile
import threading
import webbrowser
from urllib import request

from quick_tkinter import (
    EMOJI_BASE64,
    WIN_CLOSED,
    Button,
    Checkbox,
    Image,
    Multiline,
    Sizegrip,
    Text,
    Window,
    cprint,
    execute_command_subprocess,
    framework_version,
    popup,
    popup_quick_message,
    popup_yes_no,
    pysimplegui_user_settings,
    running_linux,
    running_mac,
    running_replit,
    running_trinket,
    running_windows,
    version,
)

__upgrade_server_ip = 'upgradeapi.PySimpleGUI.com'
__upgrade_server_port = '5353'

def _upgrade_gui():
    try:
        cur_ver = version[:version.index('\n')]
    except Exception:
        cur_ver = version

    if popup_yes_no("* WARNING *",
                    "You are about to upgrade your PySimpleGUI package previously installed via pip to the latest version location on the GitHub server.",
                    f"You are running verrsion {cur_ver}",
                    "",
                    "Are you sure you want to overwrite this release?", title="Are you sure you want to overwrite?",
                    keep_on_top=True) == 'Yes':
        _upgrade_from_github()
    else:
        popup_quick_message('Cancelled upgrade\nNothing overwritten', background_color='red', text_color='white', keep_on_top=True, non_blocking=False)


def _upgrade_from_github():
    mod_version = _copy_files_from_github()

    popup("*** SUCCESS ***", "PySimpleGUI.py installed version:", mod_version,
          "For python located at:", os.path.dirname(sys.executable), keep_on_top=True, background_color='red',
          text_color='white')


def __show_previous_upgrade_information():
    """
    Shows information about upgrades if upgrade information is waiting to be shown

    :return:
    """

    # if nothing to show, then just return
    if pysimplegui_user_settings.get('-upgrade info seen-', True) and not pysimplegui_user_settings.get('-upgrade info available-', False):
        return
    if pysimplegui_user_settings.get('-upgrade show only critical-', False) and pysimplegui_user_settings.get('-severity level-', '') != 'Critical':
        return

    message1 = pysimplegui_user_settings.get('-upgrade message 1-', '')
    message2 = pysimplegui_user_settings.get('-upgrade message 2-', '')
    recommended_version = pysimplegui_user_settings.get('-upgrade recommendation-', '')
    severity_level = pysimplegui_user_settings.get('-severity level-', '')

    if severity_level != 'Critical':
        return

    layout = [[Image(data=EMOJI_BASE64.HAPPY_THUMBS_UP), Text('An upgrade is available & recommended', font='_ 14')],
              [Text(f"It is recommended you upgrade to version {recommended_version}")],
              [Text(message1, enable_events=True, key='-MESSAGE 1-')],
              [Text(message2, enable_events=True, key='-MESSAGE 2-')],
              [Checkbox('Do not show this message again in the future', default_value=True, key='-SKIP IN FUTURE-')],
              [Button('Close'), Text('This window auto-closes in'), Text('30', key='-CLOSE TXT-', text_color='white', background_color='red'), Text('seconds')]]

    window = Window('PySimpleGUI Intelligent Upgrade', layout, finalize=True)
    if 'http' in message1:
        window['-MESSAGE 1-'].set_cursor('hand1')
    if 'http' in message2:
        window['-MESSAGE 2-'].set_cursor('hand1')

    seconds_left=30
    while True:
        event, values = window.read(timeout=1000)
        if event in ('Close', WIN_CLOSED) or seconds_left < 1:
            break
        if values['-SKIP IN FUTURE-']:
            if not running_trinket:
                pysimplegui_user_settings['-upgrade info available-'] = False
                pysimplegui_user_settings['-upgrade info seen-'] = True
        if event == '-MESSAGE 1-' and 'http' in message1:
            webbrowser.open_new_tab(message1)
        elif event == '-MESSAGE 2-' and 'http' in message2:
            webbrowser.open_new_tab(message2)
        window['-CLOSE TXT-'].update(seconds_left)
        seconds_left -= 1

    window.close()


def _copy_files_from_github():
    """Update the local PySimpleGUI installation from Github"""
    package_version = "Unknown"
    popup('Attempting to run the github-updater.', 'Since this is still old PSG code, the update will now exit.')
    return package_version

    github_url = 'https://raw.githubusercontent.com/PySimpleGUI/PySimpleGUI/master/'
    #files = ["PySimpleGUI.py", "setup.py"]
    files = ["PySimpleGUI.py"]

    # add a temp directory
    temp_dir = tempfile.TemporaryDirectory()
    psg_dir = os.path.join(temp_dir.name, 'PySimpleGUI')
    path = psg_dir


    os.mkdir(path)
    # path = os.path.abspath('temp')

    # download the files
    downloaded = []
    for file in files:
        with request.urlopen(github_url + file) as response, open(os.path.join(path, file), 'wb') as f:
            f.write(response.read())
            downloaded.append(file)

    # get the new version number if possible
    with open(os.path.join(path, files[0]), encoding='utf-8') as f:
        text_data = f.read()

    match = re.search(r'__version__ = \"([\d\.]+)', text_data)
    if match:
        package_version = match.group(1)

    # create a setup.py file from scratch
    setup_text = (
        "import setuptools\n"
        "setuptools.setup("
        "name='PySimpleGUI',"
        "author='PySimpleGUI',"
        "author_email='PySimpleGUI@PySimpleGUI.org',"
        "description='Unreleased Development Version',"
        "url='https://github.com/PySimpleGUI/PySimpleGUI',"
        "packages=setuptools.find_packages(),"
        f"version='{package_version}',"
        "entry_points={"
        "'gui_scripts': ["
        "'psgissue=PySimpleGUI.PySimpleGUI:main_open_github_issue',"
        "'psgmain=PySimpleGUI.PySimpleGUI:_main_entry_point',"
        "'psgupgrade=PySimpleGUI.PySimpleGUI:_upgrade_entry_point',"
        "'psghelp=PySimpleGUI.PySimpleGUI:main_sdk_help',"
        "'psgver=PySimpleGUI.PySimpleGUI:main_get_debug_data',"
        "'psgsettings=PySimpleGUI.PySimpleGUI:main_global_pysimplegui_settings',"
        "],"
        "},)"
    )

    with open(os.path.join(temp_dir.name, 'setup.py'), 'w', encoding='utf-8') as f:
        f.write(setup_text)

    # create an __init__.py file
    with open(os.path.join(path, '__init__.py'), 'w', encoding='utf-8') as f:
        f.writelines([
            'name="PySimpleGUI"\n',
            'from .PySimpleGUI import *\n',
            'from .PySimpleGUI import __version__'
        ])

    # install the pysimplegui package from local dist
    # https://pip.pypa.io/en/stable/user_guide/?highlight=subprocess#using-pip-from-your-program
    # subprocess.check_call([sys.executable, '-m', 'pip', 'install', path])
    # python_command = execute_py_get_interpreter()
    python_command = sys.executable         # always use the currently running interpreter to perform the pip!
    if 'pythonw' in python_command:
        python_command = python_command.replace('pythonw', 'python')

    layout = [[Text('Pip Upgrade Progress')],
              [Multiline(s=(90,15), key='-MLINE-', reroute_cprint=True, write_only=True, expand_x=True, expand_y=True)],
              [Button('Downloading...', key='-EXIT-'), Sizegrip()]]

    window = Window('Pip Upgrade', layout, finalize=True, keep_on_top=True, modal=True, disable_close=True, resizable=True)

    window.disable_debugger()

    cprint('The value of sys.executable = ', sys.executable, c='white on red')

    # if not python_command:
    #     python_command = sys.executable

    cprint('Installing with the Python interpreter =', python_command, c='white on purple')

    sp = execute_command_subprocess(python_command, '-m pip install', temp_dir.name,  pipe_output=True)

    threading.Thread(target=_the_github_upgrade_thread, args=(window, sp), daemon=True).start()

    while True:
        event, values = window.read()
        if event == WIN_CLOSED or (event == '-EXIT-' and window['-EXIT-'].ButtonText == 'Done'):
            break
        if event == '-THREAD-':
            cprint(values['-THREAD-'][1])
            if values['-THREAD-'][1] == '===THEAD DONE===':
                window['-EXIT-'].update(text='Done', button_color='white on red')
    window.close()
    # cleanup and remove files
    temp_dir.cleanup()


    return package_version


def execute_py_file(*, pyfile, parms=None, cwd=None, interpreter_command=None, wait=False, pipe_output=False, merge_stderr_with_stdout=True):
    """
    Executes a Python file.
    The interpreter to use is chosen based on this priority order:
        1. interpreter_command paramter
        2. global setting "-python command-"
        3. the interpreter running running PySimpleGUI
    :param pyfile:                   the file to run
    :type pyfile:                    (str)
    :param parms:                    parameters to pass on the command line
    :type parms:                     (str)
    :param cwd:                      the working directory to use
    :type cwd:                       (str)
    :param interpreter_command:      the command used to invoke the Python interpreter
    :type interpreter_command:       (str)
    :param wait:                     the working directory to use
    :type wait:                      (bool)
    :param pipe_output:              If True then output from the subprocess will be piped. You MUST empty the pipe by calling execute_get_results or your subprocess will block until no longer full
    :type pipe_output:               (bool)
    :param merge_stderr_with_stdout: If True then output from the subprocess stderr will be merged with stdout. The result is ALL output will be on stdout.
    :type merge_stderr_with_stdout:  (bool)
    :return:                         Popen object
    :rtype:                          (subprocess.Popen) | None
    """

    if cwd is None:
        # if the specific file is not found (not an absolute path) then assume it's relative to '.'
        if not os.path.exists(pyfile):
            cwd = '.'

    if pyfile[0] != '"' and ' ' in pyfile:
        pyfile = '"' + pyfile + '"'
    if interpreter_command is not None:
        python_program = interpreter_command
    else:
        # use the version CURRENTLY RUNNING if nothing is specified. Previously used the one from the settings file
        # ^ hmmm... that's not the code is doing now... it's getting the one from the settings file first
        pysimplegui_user_settings.load()        # Refresh the settings just in case they've changed via another program
        python_program = pysimplegui_user_settings.get('-python command-', '')
        if python_program == '':        # if no interpreter set in the settings, then use the current one
            python_program = sys.executable
            # python_program = 'python' if running_windows() else 'python3'
    if parms is not None and python_program:
        sp = execute_command_subprocess(python_program, pyfile, parms, wait=wait, cwd=cwd, pipe_output=pipe_output, merge_stderr_with_stdout=merge_stderr_with_stdout)
    elif python_program:
        sp = execute_command_subprocess(python_program, pyfile, wait=wait, cwd=cwd, pipe_output=pipe_output, merge_stderr_with_stdout=merge_stderr_with_stdout)
    else:
        print('execute_py_file - No interpreter has been configured')
        sp = None
    return sp


def _main_entry_point():
    # print('Restarting main as a new process...(needed in case you want to GitHub Upgrade)')
    # Relaunch using the same python interpreter that was used to run this function
    interpreter = sys.executable
    if 'pythonw' in interpreter:
        interpreter = interpreter.replace('pythonw', 'python')
    execute_py_file(__file__, interpreter_command=interpreter)


def _the_github_upgrade_thread(window:Window, sp):
    """
    The thread that's used to run the subprocess so that the GUI can continue and the stdout/stderror is collected

    :param window:
    :param sp:
    :return:
    """

    window.write_event_value('-THREAD-', (sp, '===THEAD STARTING==='))
    window.write_event_value('-THREAD-', (sp, '----- STDOUT & STDERR Follows ----'))
    for line in sp.stdout:
        oline = line.decode().rstrip()
        window.write_event_value('-THREAD-', (sp, oline))

    # DO NOT CHECK STDERR because it won't exist anymore. The subprocess code now combines stdout and stderr
    # window.write_event_value('-THREAD-', (sp, '----- STDERR ----'))

    # for line in sp.stderr:
    #     oline = line.decode().rstrip()
    #     window.write_event_value('-THREAD-', (sp, oline))
    window.write_event_value('-THREAD-', (sp, '===THEAD DONE==='))


def _upgrade_entry_point():
    """
    This function is entered via the psgupgrade.exe file.

    It is needed so that the exe file will exit and thus allow itself to be overwritten which
        is what the upgrade will do.
    It simply runs the PySimpleGUI.py file with a command line argument "upgrade" which will
        actually do the upgrade.
    """
    interpreter = sys.executable
    if 'pythonw' in interpreter:
        interpreter = interpreter.replace('pythonw', 'python')
    execute_py_file(__file__, 'upgrade', interpreter_command=interpreter)

def __perform_upgrade_check_thread():
    # print(f'Upgrade thread...seen = {pysimplegui_user_settings.get("-upgrade info seen-", False)}')
    try:
        if running_trinket:
            os_name = 'Trinket'
            os_ver = __get_linux_distribution()
        elif running_replit:
            os_name = 'REPL.IT'
            os_ver = __get_linux_distribution()
        elif running_windows:
            os_name = 'Windows'
            os_ver = platform.win32_ver()
        elif running_linux:
            os_name = 'Linux'
            os_ver = __get_linux_distribution()
        elif running_mac:
            os_name = 'Mac'
            os_ver = platform.mac_ver()
        else:
            os_name = 'Other'
            os_ver = ''

        psg_ver = version
        framework_ver = framework_version
        python_ver = sys.version

        upgrade_dict = {
            'OSName' : str(os_name),
            'OSVersion' : str(os_ver),
            'PythonVersion' : str(python_ver),
            'PSGVersion' : str(psg_ver),
            'FrameworkName' : 'tkinter',
            'FrameworkVersion' : str(framework_ver),
        }
        reply_data = __send_dict(__upgrade_server_ip, __upgrade_server_port, upgrade_dict)

        recommended_version = reply_data.get('SuggestedVersion', '')
        message1 = reply_data.get('Message1', '')
        message2 = reply_data.get('Message2', '')
        severity_level = reply_data.get('SeverityLevel', '')
        # If any part of the reply has changed from the last reply, overwrite the data and set flags so user will be informed
        if (message1 or message2) and not running_trinket:
            if pysimplegui_user_settings.get('-upgrade message 1-', '') != message1 or \
               pysimplegui_user_settings.get('-upgrade message 2-', '') != message2 or \
               pysimplegui_user_settings.get('-upgrade recommendation-', '') != recommended_version or \
               pysimplegui_user_settings.get('-severity level-', '') != severity_level:
                # Save the data to the settings file
                pysimplegui_user_settings['-upgrade info seen-'] = False
                pysimplegui_user_settings['-upgrade info available-'] = True
                pysimplegui_user_settings['-upgrade message 1-'] = message1
                pysimplegui_user_settings['-upgrade message 2-'] = message2
                pysimplegui_user_settings['-upgrade recommendation-'] = recommended_version
                pysimplegui_user_settings['-severity level-'] = severity_level
    except Exception:
        reply_data = {}
        # print('Upgrade server error', e)
    # print(f'Upgrade Reply = {reply_data}')


def __get_linux_distribution():
    line_tuple = ('Linux Distro', 'Unknown', 'No lines Found in //etc//os-release')
    try:
        with open('/etc/os-release') as f:
            data = f.read()
        lines = data.split('\n')
        for line in lines:
            if line.startswith('PRETTY_NAME'):
                line_split = line.split('=')[1].strip('"')
                return tuple(line_split.split(' '))
    except Exception:
        line_tuple = ('Linux Distro', 'Exception','Error reading//processing //etc//os-release')

    return line_tuple


def __perform_upgrade_check():
    # For now, do not show data returned. Still testing and do not want to "SPAM" users with any popups
    __show_previous_upgrade_information()
    threading.Thread(target=__perform_upgrade_check_thread, daemon=True).start()

def __send_dict(ip, port, dict_to_send):
    """
    Send a dictionary to the upgrade server and get back a dictionary in response
    :param ip:           ip address of the upgrade server
    :type ip:            str
    :param port:         port number
    :type port:          int | str
    :param dict_to_send: dictionary of items to send
    :type dict_to_send:  dict
    :return:             dictionary that is the reply
    :rtype:              dict
    """

    # print(f'sending dictionary to ip {ip} port {port}')
    try:
        # Create a socket object
        s = socket.socket()

        s.settimeout(5.0)       # set a 5 second timeout

        # connect to the server on local computer
        s.connect((ip , int(port)))
        # send a python dictionary
        s.send(json.dumps(dict_to_send).encode())

        # receive data from the server
        reply_data = s.recv(1024).decode()
        # close the connection
        s.close()
    except Exception as e:
        # print(f'Error sending to server:', e)
        # print(f'payload:\n', dict_to_send)
        reply_data = e
    try:
        data_dict = json.loads(reply_data)
    except Exception:
        # print(f'UPGRADE THREAD - Error decoding reply {reply_data} as a dictionary. Error = {e}')
        data_dict = {}
    return data_dict
