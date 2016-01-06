"""The Interactive Movie Renamer.

Point this at a directory full of movie files, and you can look them up on the OMDb ("Open Movie Database") and move
each into its own folder, with a folder.jpg file of the poster. It will rename the movie file to just the movie title,
and the folder name will be "Movie Name (YYYY)".

Simply run the script from a command line to get started.

There are a few steps:

1. Type in the directory. It will remember the last one entered.
2. For each movie, we first query the OMDb with a guess from the file name.
   * If that works, then we can choose one of the entries to use, or enter new search terms, or enter 0 to skip.
   * If that fails (no results), then we enter new search terms, or leave blank to skip.
3. Repeat until done.

Future improvements:
* Handle multiple movie files.
* OMDb doesn't always find the right movie (e.g. Pride and Prejudice, 2005 version). Search by year, too, maybe?
* Better source for pictures (themoviedb.org, maybe, but you have to apply for an API key).
* Customization, such as movie name, whether or not to put in subfolder, etc.
* Going through and fixing up previously done movies (i.e. looking in subfolders).
* Option to remove non-ASCII characters, or change forbidden characters (i.e. for UNIX).

"""

from __future__ import absolute_import, unicode_literals

import pickle
import logging
import os
import shutil
import requests

pickle_file = 'renamer_data.pickle'
omdb_url = 'http://www.omdbapi.com/'
forbidden_characters = r'<>/\:"|?*'


def rename(directory):
    """Run the renamer.

    Args:
        directory (str): relative or absolute path to the directory containing movies.

    Returns:

    """
    old_dir = os.getcwd()
    os.chdir(directory)
    files = [f for f in os.listdir('.') if os.path.isfile(f) and not f.startswith('.')]
    for f in files:
        rename_movie(f)

    os.chdir(old_dir)


def rename_movie(filename, search_string=None, page=1):
    """Move/rename a given movie file.

    Args:
        filename (unicode): original file name
        search_string (str or None): search to perform on OMDB. if None, construct one from the filename.
        page (int): what page of results to get
    """
    if not search_string:
        search_string = construct_search(filename)
    search = requests.get(omdb_url, {'s': search_string, 'page': page})
    json = search.json()
    while 'Error' in json:
        search_string = raw_input(
            "Error for \"{}\": {} Enter new search terms, or leave blank to skip: ".format(filename, json['Error'])
        )
        if not search_string:
            return
        json = requests.get(omdb_url, {'s': search_string, 'page': page}).json()
    print_list(json, filename)
    print
    choice = raw_input("Choose one, or enter new search terms: ")
    if choice == 'n':
        return rename_movie(filename, search_string, page=page+1)
    try:
        num = int(choice)
        if num == 0:
            return
        entry = json['Search'][num-1]
    except (ValueError, IndexError):
        return rename_movie(filename, search_string=choice)
    perform_rename(filename, entry)


def perform_rename(filename, entry):
    """Rename the given file with the entry selected by the user.

    Args:
        filename (unicode): original filename
        entry (dict): entry from json response selected by user
    """
    new_dir = _clean("{} ({})".format(entry['Title'], entry['Year']))
    if os.path.exists(new_dir):
        logging.error("{} already exists.".format(new_dir))
        return
    file_type = filename.rpartition('.')[-1]
    new_name = os.path.join(new_dir, _clean("{}.{}".format(entry['Title'], file_type)))
    os.mkdir(new_dir)
    shutil.move(filename, new_name)
    os.chdir(new_dir)
    if 'Poster' in entry:
        if entry['Poster'] == 'N/A':
            logging.warn("No poster available for {}".format(new_name))
        else:
            file_type = entry['Poster'].rpartition('.')[-1]
            poster_name = 'folder.' + file_type
            poster_resp = requests.get(entry['Poster'])
            with open(poster_name, 'wb') as f:
                f.write(poster_resp.content)
    os.chdir('..')


def print_list(json, filename):
    """Print list of entries for user to choose from.

    Args:
        json (dict): json response from OMDB
        filename (unicode): original filename
    """
    print
    print 'Choose entry for "{}"'.format(filename)
    print "  0: Skip this file"
    for i, entry in enumerate(json['Search']):
        print "  {}: {} ({}) [{}]".format(i+1, entry['Title'], entry['Year'], entry['Type'])
    print "  n: Next page of results"


def construct_search(filename):
    """Construct a search string from a filename.

    We remove the file extension and replace some characters with spaces.

    Args:
        filename (unicode): original file name

    Returns:
        str: search string
    """
    s = filename.rpartition('.')[0]
    s = s.replace('.', ' ')
    return s


def get_directory():
    """Query the user for a directory.

    Returns:
        str: a path to a directory.
    """
    last = _lookup_last_dir()
    inp = raw_input('Directory with files for renaming ({}): '.format(last))
    if not inp:
        inp = last
    _save_dir(inp)
    return inp


def _lookup_last_dir():
    """Look up the last dir used from the pickle.

    Returns:
        str: last directory used.
    """
    return _load_pickle().get('last_directory', '')


def _save_dir(directory):
    """Save this directory to the pickle

    Args:
        directory (unicode): directory to save

    Returns:
        None
    """
    data = _load_pickle()
    data['last_directory'] = directory
    _save_pickle(data)


def _save_pickle(data):
    try:
        with open(pickle_file, 'w') as f:
            pickle.dump(data, f)
    except EnvironmentError:
        logging.warn("Unable to save pickle to {}".format(pickle_file))


def _load_pickle():
    try:
        with open(pickle_file) as f:
            data = pickle.load(f)
    except EnvironmentError:
        data = {}
    return data


def _clean(filename):
    """Remove illegal filename characters; uses forbidden_characters global.

    Currently only removes characters forbidden on Windows.

    Args:
        filename (unicode): filename to clean

    Returns:
        unicode: cleaned filename
    """
    for x in forbidden_characters:
        filename = filename.replace(x, ' ')
    while '  ' in filename:
        filename = filename.replace('  ', ' ')
    return filename

if __name__ == '__main__':
    rename(get_directory())
