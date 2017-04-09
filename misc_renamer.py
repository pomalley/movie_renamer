"""Miscellaneous moving/renaming functions.

organize_gog: use on a directory with GoG installer downloads/backups

"""

import os
import shutil
import logging


def organize_gog(path, dry_run=False):
    """Move GoG installers into their own subfolders.

    Takes a file named setup_[game]_[version].[exe/bin] and moves it into its own subfolder.

    Args:
        path (str): directory with files.
        dry_run (bool): if True, do not actually rename.
    """
    for f in os.listdir(path):
        if not os.path.isfile(os.path.join(path, f)):
            logging.debug("Skipping {}".format(f))
            continue
        logging.debug("Processing {}".format(f))
        sections = f.split('_')
        if sections[0] != 'setup':
            continue
        dir_path = os.path.join(path, '_'.join(sections[1:-1]))
        if not os.path.exists(dir_path) and not dry_run:
            os.mkdir(dir_path)
        if not (os.path.isdir(dir_path) or (dry_run and not os.path.exists(dir_path))):
            logging.error("{} exists and is not a directory.".format(dir_path))
            continue
        if not dry_run:
            shutil.move(os.path.join(path, f), dir_path)
        logging.info("{} moved to {}.".format(f, dir_path))
