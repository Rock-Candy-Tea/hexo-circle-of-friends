from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter

# from prompt_toolkit.lexers import PygmentsLexer
# from pygments.lexers.sql import SqlLexer

fcircle_token = {
    "fcircle": {
        "run": {
            "server": None,
            "docker": None
        },
        "rm": {
            "server": None,
            "docker": None
        }
    },
    "exit": None,
    "quit": None
}
fcircle_completer = NestedCompleter.from_nested_dict(fcircle_token)


def main():
    session = PromptSession(completer=fcircle_completer)

    while True:
        try:
            text = session.prompt('> ')
            if text in ("quit", "exit"):
                break
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        else:
            print(text)

    print('GoodBye!')


if __name__ == '__main__':
    main()
