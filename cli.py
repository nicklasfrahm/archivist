from argparse import ArgumentParser
from threading import Lock
from sys import stdout
from unzip import Unzipper
from time import sleep
import index

# A mutex to prevent simultaneous access to the console screen.
console_screen = Lock()


def clear():
    """Clear the console."""
    stdout.write("\033[2J\033[H")


def index_func(args):
    """Index the directory tree."""
    global threads

    index.start()

    try:
        while True:
            console_screen.acquire()
            index.display_progress()
            console_screen.release()

            time.sleep(0.50)

    except KeyboardInterrupt:
        print()
        # index.terminate_workers()
        exit(1)


def unzip_func(args):
    """Extract all archives from folder."""
    global console_screen

    unzip = Unzipper(args.folder, args.out, args.done)
    scanned = False
    detected = 0

    try:
        while True:
            # Scan once or continuously if the watch mode is enabled.
            if args.watch or not scanned:
                detected = unzip.scan()
                scanned = True

            # Check if all archives have been unzipped.
            if not args.watch and unzip.idle():
                if detected > 0:
                    clear()
                stdout.write(f"Processed archives: {detected}\n")
                return

            # Print progress to screen.
            console_screen.acquire()
            output = unzip.report()
            if output:
                # The process has new information.
                clear()
                stdout.write(output)
            elif output is None:
                # The process is idle.
                clear()
                stdout.write("Scanning for archives ...\n")
            console_screen.release()

            # Delay next iteration to prevent excessive folder polling.
            sleep(0.50)

    except KeyboardInterrupt:
        print()
        unzip.abort()
        exit()


if __name__ == "__main__":
    # Basic information about the program.
    prog = "cli.py"
    description = "Process large amounts of files and folders."

    # Scaffolding for the command line interface.
    cli = ArgumentParser(prog=prog, description=description)
    cli.set_defaults(func=lambda args: cli.print_help())
    cli_subparsers = cli.add_subparsers(help="Display subcommand help.")

    # The info subcommand.
    cli_index = cli_subparsers.add_parser("index", help="Index the directory.")
    cli_index.add_argument("folder", nargs="?", default=".", help="Directory to index.")
    cli_index.set_defaults(func=index_func)

    # The unzip subcommand.
    cli_unzip = cli_subparsers.add_parser(
        "unzip", help="Extract all archives from folder."
    )
    cli_unzip.add_argument(
        "folder", nargs="?", default=".", help="Folder with archives to process."
    )
    cli_unzip.add_argument(
        "-o",
        default="out",
        help="Folder to unzip archives to.",
        metavar="OUT",
        dest="out",
    )
    cli_unzip.add_argument(
        "-d",
        default="done",
        help="Folder for processed archives.",
        metavar="DONE",
        dest="done",
    )
    cli_unzip.add_argument(
        "-w",
        default=False,
        help="Watch folder for archives.",
        action="store_true",
        dest="watch",
    )
    cli_unzip.set_defaults(func=unzip_func)

    # Parse arguments and run according function.
    args = cli.parse_args()
    args.func(args)
