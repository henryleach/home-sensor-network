import sqlite3
from datetime import datetime, timezone
import os
import argparse
import tarfile

""" Basically just a wrapping of the example https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup """

def copy_progress(status, remaining, total):
    """ Show the progress of the DB copying. """
    print(f"Copied {total-remaining} of {total} pages.")


def backup_db(src_path, dest_path):
    """ Copy the contents of DB at src_path into
        DB at des_path, creating if it doesn't exist
    """

    # Try using the URI method to open the DB as read only
    # Does this help prevent conflicts, or is that only
    # on a transaction basis anyway?
    uri_path = "file:" + src_path + "?mode=ro"
    with sqlite3.connect(uri_path, uri=True) as src:
        print(f"Opening: {src_path}")
        with sqlite3.connect(dest_path) as dest:
            src.backup(dest, pages=100, progress=copy_progress)

    print(f"DB copy complete.")
    return None


def create_backup_name(source):
    """ Create the name of the backup file
        based on the current utc time.
    """

    filename = os.path.basename(source)

    now_utc = datetime.now(timezone.utc)
    now_str = now_utc.strftime("%Y-%m-%dT%H%M%Sutc")
    
    backup_name = now_str + "-" + filename

    return backup_name

    

def main():

    prog_desc = ("Create zipped backup of an sqlite3 DB,"
                 " that is safe to run on DB being accessed by others. "
                 "Defaults to creating the backup "
                 "in the same directory as source with timestamp "
                 "prefixed to name.")
    
    parser = argparse.ArgumentParser(prog="backup-sqlite-db",
                                     description=prog_desc)
    parser.add_argument("source",
                        help=("Sqlite3 DB to back up."))
    parser.add_argument("-d", "--outdir",
                        help=("Specify the directory "
                              "in which to save the backup."))
    parser.add_argument("-o", "--outfile",
                        help=("Specify the whole output "
                              "path and filename."))
    # out-file supersedes out-dir                                 

    args = parser.parse_args()

    # Create the various out options.
    abs_src_path = os.path.abspath(args.source)
    
    if args.outfile:
        out_db = os.path.abspath(args.outfile)

    elif args.outdir:
        out_path = os.path.abspath(args.outdir)
        out_db = os.path.join(out_path, create_backup_name(args.source))
    else:
        # Nothing specified, create in local dir
        out_path = os.path.dirname(abs_src_path)
        out_db = os.path.join(out_path, create_backup_name(args.source))
        
    # print(f"Output to: {out_db}")
    
    backup_db(abs_src_path, out_db)

    # Specifying an arcname prevents the whole preceding
    # directory structure being copied.
    with tarfile.open((out_db + ".tar.gz"), "w:gz") as tar:
        tar.add(out_db, arcname=os.path.basename(out_db))
        
    print(f"Wrote: {out_db + '.tar.gz'}")   

    
    # Delete the temporary unzipped backup
    os.remove(out_db)

if __name__ == "__main__":
    main()
