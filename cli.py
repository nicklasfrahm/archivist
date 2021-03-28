from argparse import ArgumentParser
import os, sys, stat, math, time, threading
import unzip

size = 0
dirs = 0
files = 0
extensions = {}
unknown_paths = []
threads = []

# A mutex to prevent simultaneous access to the console screen.
console_screen = threading.Lock()


def clear():
    """Clear the whole console."""
    stdout.write("\033[2J\033[H")


def no_op(file, info):
    """An empty function that does nothing."""


def walk_tree(location, on_file=no_op, on_dir=no_op):
    """Recursively descend the directory tree rooted at location. Calls the
    `on_file` callback for every file and the `on_dir` callback for every
    directory."""
    global threads

    for item in os.listdir(location):
        pathname = os.path.join(location, item)
        stat_info = os.stat(pathname)
        if stat.S_ISDIR(stat_info.st_mode):
            # It's a directory, call the `on_dir` callback and recurse into it.
            on_dir(pathname, stat_info)

            # Start a new thread to walk the subdirectory.
            t = threading.Thread(
                target=walk_tree,
                args=(
                    pathname,
                    on_file,
                    on_dir,
                ),
            )
            threads.append(t)
            t.start()
        elif stat.S_ISREG(stat_info.st_mode):
            # It's a file, call the `on_dir` callback.
            on_file(pathname, stat_info)
        else:
            # Unknown file type, add to `unknown_paths`.
            unknown_paths.append(pathname)


def display_info():
    """Update the display of the currently analysed files."""
    global files, dirs, size, threads, screen

    screen.acquire()

    clear()
    print(f"Treads: {len(threads)}")
    print(f"Directories: {dirs}")
    print(f"Files: {files}")
    print(f"Size: {human_size(size)}")

    screen.release()


def info_file(pathname, file_info):
    global files, size

    files += 1
    size += file_info.st_size
    display_info()


def info_dir(pathname, dir_info):
    global dirs, dirpaths

    dirs += 1
    display_info()


def info_func(args):
    """Analyse the directory tree."""
    global threads

    try:
        walk_tree(args.dir, info_file, info_dir)

        for t in threads:
            t.join()
    except KeyboardInterrupt:
        print(unknown_paths)
        exit(1)


def unzip_func(args):
    """Extract all archives from folder."""
    global console_screen

    scan = True

    try:
        while True:

            # Scan once or continously if the watch mode is enabled.
            if args.watch or scan:
                for pathname in os.listdir(args.dir):
                    segments = pathname.rsplit(".", 1)

                    if len(segments) == 2:
                        name = segments[0]
                        extension = segments[1].lower()

                        if extension == "zip":
                            unzip.create_worker(pathname, args)

                scan = False

            # Check if all archives have been unzipped.
            if not args.watch and unzip.idle():
                return

            console_screen.acquire()
            unzip.display_progress()
            console_screen.release()

            time.sleep(0.50)

    except KeyboardInterrupt:
        print()
        unzip.terminate_workers()
        exit()


if __name__ == "__main__":
    # Basic information about the program.
    prog = "archivist.py"
    description = "Process large amounts of files and folders."

    # Scaffolding for the command line interface.
    cli = ArgumentParser(prog=prog, description=description)
    cli.set_defaults(func=lambda args: cli.print_help())
    cli_subparsers = cli.add_subparsers(help="Display subcommand help.")

    # The info subcommand.
    cli_info = cli_subparsers.add_parser("info", help="Analyse the directory.")
    cli_info.add_argument("dir", nargs="?", default=".", help="Directory to analyse.")
    cli_info.set_defaults(func=info_func)

    # The unzip subcommand.
    cli_unzip = cli_subparsers.add_parser(
        "unzip", help="Extract all archives from folder."
    )
    cli_unzip.add_argument(
        "dir", nargs="?", default=".", help="Folder with archives to process."
    )
    cli_unzip.add_argument(
        "-o",
        default="out",
        help="Folder to unzip archives to.",
        metavar="out_dir",
        dest="out",
    )
    cli_unzip.add_argument(
        "-d",
        default="done",
        help="Folder for processed archives.",
        metavar="done_dir",
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
