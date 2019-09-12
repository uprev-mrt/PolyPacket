#!/usr/bin/python3
"""
An example of a BufferControl in a full screen layout that offers auto
completion.
Important is to make sure that there is a `CompletionsMenu` in the layout,
otherwise the completions won't be visible.
"""
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.widgets import SearchToolbar, TextArea
from prompt_toolkit.layout.containers import (
    Float,
    FloatContainer,
    HSplit,
    Window,
)
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu

# The completer.
command_completer = WordCompleter([
    'connect', 'send'], ignore_case=True)

packet_completer= WordCompleter(['SendCmd', 'Data', 'Ping'], ignore_case=True)

data_field_completer= WordCompleter(['sensorA', 'sensorB','sensorName'], ignore_case=True)

sendcmd_field_completer= WordCompleter(['cmd'], ignore_case=True)


fieldDict = {
    'SendCmd':['cmd'],
    'Data': ['sensorA', 'sensorB','sensorName']
};

command_completer = WordCompleter([
    'alligator', 'ant', 'ape', 'bat', 'bear', 'beaver', 'bee', 'bison',
    'butterfly', 'cat', 'chicken', 'crocodile', 'dinosaur', 'dog', 'dolphin',
    'dove', 'duck', 'eagle', 'elephant', 'fish', 'goat', 'gorilla', 'kangaroo',
    'leopard', 'lion', 'mouse', 'rabbit', 'rat', 'snake', 'spider', 'turkey',
    'turtle',
], ignore_case=True)


outputBuffer = Buffer(multiline=True)

def onInputChange(buff):
    input = buff
    outputBuffer += word +"\n"
    # if input[:1] == ' ':
    #     word = input.split()[-1]
    #     outputBuffer += word +"\n"
        # if word in fieldDict:
        #     buff.completer = WordCompleter(fieldDict[word],ignore_case=True )

# The layout
inputBuffer = Buffer(completer=command_completer, complete_while_typing=False, multiline=False, on_text_changed=onInputChange)
#inputBuffer.text = '>>>'

outputWin = Window(BufferControl(buffer=outputBuffer,focusable=False), height=14, style='reverse')
inputWin = Window(BufferControl(buffer=inputBuffer))
body = FloatContainer(
    content=HSplit([
        outputWin,
        inputWin,
    ]),
    floats=[
        Float(xcursor=True,
              ycursor=True,
              content=CompletionsMenu(max_height=16, scroll_offset=1))
    ]
)


# Key bindings
kb = KeyBindings()


@kb.add('q')
@kb.add('c-c')
def _(event):
    " Quit application. "
    event.app.exit()

@kb.add('enter')
def _(event):
    new_text =outputBuffer.text + "\n"+ inputBuffer.text
    outputBuffer.text = new_text
    inputBuffer.text = '>>> '



#buff.on_text_changed = onInputChange;

# The `Application`
application = Application(
    layout=Layout(body),
    key_bindings=kb,
    full_screen=True)


def run():
    application.run()


if __name__ == '__main__':
    run()
