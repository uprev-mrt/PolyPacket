#!/usr/bin/python3

from prompt_toolkit.application import Application
from prompt_toolkit.document import Document
from prompt_toolkit.filters import has_focus
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import SearchToolbar, TextArea
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion import FuzzyWordCompleter
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl

import sys
import os

# from polypacket.protocol import *
# from polypacket.polyservice import *



help_text = """
Type any expression (e.g. "4 + 4") followed by enter to execute.
Press Control-C to exit.
"""

command_completer = FuzzyWordCompleter(['connect','send'])



animal_completer = FuzzyWordCompleter([
    'alligator', 'ant', 'ape', 'bat', 'bear', 'beaver', 'bee', 'bison',
    'butterfly', 'cat', 'chicken', 'crocodile', 'dinosaur', 'dog', 'dolphin',
    'dove', 'duck', 'eagle', 'elephant', 'fish', 'goat', 'gorilla', 'kangaroo',
    'leopard', 'lion', 'mouse', 'rabbit', 'rat', 'snake', 'spider', 'turkey',
    'turtle',])

color_completer = FuzzyWordCompleter(['red', 'blue', 'green', 'orange', 'purple', 'yellow', 'cyan',
          'magenta', 'pink'])

#
# def load_protocol(protocolFile):
#     protocol = buildProtocol(protocolFile)

    #


def main():

    # The layout.
    #search_field = SearchToolbar()  # For reverse search.

    output_field = TextArea(style='class:output-field', text=help_text)

    input_field = TextArea(
        height=14, prompt='>>> ', style='class:input-field', multiline=False,
        wrap_lines=False,completer=animal_completer,
                  complete_while_typing=False)

    status_field = TextArea(
        height=1, style='class:status', multiline=False,wrap_lines=False)

    autocomp_area = TextArea(wrap_lines=False, read_only=True)

    container = HSplit([
        output_field,
        Window(height=1, char='-', style='class:line'),
        input_field,
        autocomp_area,
        status_field,
    ])

    # Attach accept handler to the input field. We do this by assigning the
    # handler to the `TextArea` that we created earlier. it is also possible to
    # pass it to the constructor of `TextArea`.
    # NOTE: It's better to assign an `accept_handler`, rather then adding a
    #       custom ENTER key binding. This will automatically reset the input
    #       field and add the strings to the history.
    def accept(buff):
        # Evaluate "calculator" expression.
        new_text =output_field.text + "\n"+ input_field.text
        input_field.completer =color_completer

        # Add text to output buffer.
        output_field.buffer.document = Document(
            text=new_text, cursor_position=len(new_text))

    input_field.accept_handler = accept

    # The key bindings.
    kb = KeyBindings()

    @kb.add('c-c')
    @kb.add('c-q')
    def _(event):
        " Pressing Ctrl-Q or Ctrl-C will exit the user interface. "
        event.app.exit()

    # Style.
    style = Style([
        ('output-field', 'bg:#000000 #ffffff'),
        ('input-field', 'bg:#000000 #ffffff'),
        ('line',        '#004400'),
        ('status', 'bg:#004400 #ffffff')
    ])

    # Run application.
    application = Application(
        layout=Layout(container, focused_element=input_field),
        key_bindings=kb,
        style=style,
        mouse_support=True,
        full_screen=True)

    application.run()


if __name__ == '__main__':
    main()
