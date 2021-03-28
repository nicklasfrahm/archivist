from threading import Thread
from zipfile import ZipFile
from copy import deepcopy
from shutil import move
from os import system, path, makedirs, cpu_count, listdir, stat
from stat import S_ISREG
import math


def human_filesize(filesize):
    """Display the filesize in a human-readable unit."""
    if filesize > 0:
        names = [" ", "k", "M", "G", "T", "P", "E"]
        exponent = math.floor(math.log(filesize, 1000))
        digits = filesize / math.pow(1000, exponent)
        prefix = names[exponent]

        return "%6.2f %sB" % (digits, prefix)
    else:
        return "  0.00  B"


class Unzipper:
    """A class to unzip a folder of archives."""

    def __init__(
        self,
        dir_in=".",
        dir_out="out",
        dir_done="done",
        concurrency=cpu_count() - 1,
    ):
        self.dir_in = dir_in
        self.dir_out = dir_out
        self.dir_done = dir_done

        # Concurrency limit of the unzip operations.
        self.concurrency = concurrency

        # Dictionaries to hold the current progress and
        # size meta data of all unzip operations. Indexed
        # by the name of the processed file.
        self.progress = {}
        self.size = {}

        # A flag to indicate if the worker threads should abort the operation.
        self.aborted = False

    def worker(self, pathname):
        """Unzips an archive and updates the progress."""
        # Track progress.
        self.progress.update({pathname: float(0)})

        try:
            zf = ZipFile(pathname)
            uncompressed = float(sum((f.file_size for f in zf.infolist())))
            extracted = float(0)

            self.size.update({pathname: uncompressed})

            for f in zf.infolist():
                if self.aborted:
                    return

                zf.extract(member=f, path=self.dir_out)

                extracted += float(f.file_size)
                if uncompressed > 0:
                    self.progress.update({pathname: extracted * 100 / uncompressed})

            self.size.pop(pathname)

            try:
                makedirs(self.dir_done)
            except:
                # Ignore errors while trying to create directory.
                pass

            try:
                move(pathname, path.join(self.dir_done, pathname))
            except Exception as err:
                # Ignore errors while trying to move file.
                pass

        except Exception as err:
            pass
        finally:
            self.progress.pop(pathname)

    def spawn(self, pathname):
        """Spawn a new worker thread to unzip the file if no
        unzip operation is currently in progress for this file."""

        if self.concurrency > len(self.progress):
            if self.progress.get(pathname) is None:
                t = Thread(target=self.worker, args=(pathname,))
                t.start()

    def report(self):
        """Create a progress report of all unzip operations."""

        snapshot_size = deepcopy(self.size)
        snapshot_progress = deepcopy(self.progress)

        if len(snapshot_size) > 0:
            info = ""

            for filename in sorted(list(snapshot_progress)):
                progress = snapshot_progress.get(filename) or 0
                info += "%6.2f %%" % progress

                total = snapshot_size.get(filename) or 0
                current = progress * total / 100
                info += f"    {human_filesize(current)} / {human_filesize(total)}"

                info += f"    {filename}\n"

            return info

        else:
            # Indicate idle state.
            return None

    def abort(self):
        """Sets the `abort` flag to interrupt running workers."""
        self.aborted = True

    def idle(self):
        """Returns `True` if no files are currently being processed."""
        return len(self.progress) == 0

    def scan(self):
        """Scan files in input folder and start new unzip workers for every archive found."""
        detected = 0

        for pathname in listdir(self.dir_in):
            segments = pathname.rsplit(".", 1)
            statinfo = stat(pathname)

            if S_ISREG(statinfo.st_mode) and len(segments) == 2:
                extension = segments[1].lower()
                if extension == "zip":
                    detected += 1
                    self.spawn(pathname)

        return detected
