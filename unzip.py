from threading import Thread
from zipfile import ZipFile
from copy import deepcopy
from shutil import move
from os import system, path, makedirs, cpu_count
from sys import stdout
import math

# Holds the names and the current progress of all unzip operations.
zip_file_progress = {}
zip_file_size = {}
terminate = False


def clear():
    """Clear the console."""
    stdout.write("\033[2J\033[H")


def human_filesize(filesize):
    """Display the filesize in a human-readable unit,
    while not exceeding two digits before the decimal."""
    golden_ratio = 2.0 / 3.0

    if filesize > 0:
        names = [" ", "k", "M", "G", "T", "P", "E"]
        exponent = math.log(filesize, 1000)

        # Never display more than two digits before the decimal.
        if exponent - math.floor(exponent) < golden_ratio:
            exponent = math.floor(exponent)
        else:
            exponent = math.ceil(exponent)

        return "%5.2f %sB" % (filesize / math.pow(1000, exponent), names[exponent])

    else:
        return "00.00  B"


def unzip_worker(pathname, config):
    """Unzip an archive and update the progress."""
    global zip_file_progress, terminate

    # Track progress.
    zip_file_progress.update({pathname: float(0)})

    try:
        zf = ZipFile(pathname)
        uncompressed = float(sum((f.file_size for f in zf.infolist())))
        extracted = float(0)

        zip_file_size.update({pathname: uncompressed})

        for f in zf.infolist():
            if terminate:
                return

            zf.extract(member=f, path=config.out)

            extracted += float(f.file_size)
            if uncompressed > 0:
                zip_file_progress.update({pathname: extracted * 100 / uncompressed})

        zip_file_size.pop(pathname)

        try:
            makedirs(config.done)
        except:
            # Ignore errors while trying to create directory.
            pass

        try:
            move(pathname, path.join(config.done, pathname))
        except Exception as err:
            # Ignore errors while trying to move file.
            pass

    except Exception as err:
        pass
    finally:
        zip_file_progress.pop(pathname)


def create_worker(pathname, config):
    """Create a new worker thread to unzip the file if no
    unzip operation is currently in progress for this file."""
    global zip_file_progress

    if cpu_count() // 2 > len(zip_file_progress):
        if zip_file_progress.get(pathname) is None:
            t = Thread(target=unzip_worker, args=(pathname, config))
            t.start()


def display_progress():
    """Display the progress of all unzip operations."""
    global zip_file_progress, zip_file_size

    snapshot_size = deepcopy(zip_file_size)
    snapshot_progress = deepcopy(zip_file_progress)

    if len(snapshot_size) > 0:
        if len(snapshot_size) == len(snapshot_progress):
            clear()

            info = ""

            for filename in sorted(list(snapshot_progress)):
                progress = snapshot_progress.get(filename)
                info += "%6.2f %%" % progress

                total = snapshot_size.get(filename)
                current = progress * total / 100
                info += f"\t{human_filesize(current)} / {human_filesize(total)}"

                info += f"\t{filename}\n"

            print(info)

    else:
        clear()
        print("Watching for archives ...")


def terminate_workers():
    """Sets the terminate flags to stop workers."""
    global terminate

    terminate = True


def idle():
    """Returns true if no files are currently being processed."""
    global zip_file_progress

    return len(zip_file_progress) == 0