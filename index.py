import os, sys, stat, math, time, threading

import sqlite3

# con = sqlite3.connect("example.db")
# cur = con.cursor()


def clear():
    """Clear the whole console."""
    stdout.write("\033[2J\033[H")


size = 0
dirs = 0
files = 0
extensions = {}
unknown_paths = []
threads = []


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

        # if stat.S_ISDIR(stat_info.st_mode):
        #     # It's a directory, call the `on_dir` callback and recurse into it.
        #     on_dir(pathname, stat_info)

        #     # Start a new thread to walk the subdirectory.
        #     t = threading.Thread(
        #         target=walk_tree,
        #         args=(
        #             pathname,
        #             on_file,
        #             on_dir,
        #         ),
        #     )
        #     threads.append(t)
        #     t.start()
        # elif stat.S_ISREG(stat_info.st_mode):
        #     # It's a file, call the `on_dir` callback.
        #     on_file(pathname, stat_info)
        # else:
        #     # Unknown file type, add to `unknown_paths`.
        #     unknown_paths.append(pathname)


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
