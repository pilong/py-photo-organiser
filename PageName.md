
```

Organise your photos.

NAME
    photo-organiser - sorting photo files according to their picture take date

SYNOPSIS
    [python] photo-organiser [OPTION]... [SOURCE] [DESTINATION]

EXAMPLE
    [python] photo-organiser [-r] [-v]

DESCRIPTION
    copy or move a directory tree of photos recursively and put the photos into
    direcctories of their own date. A photo file that was taken at YYYY/MM/DD
    will end up in a folder of YYYY/MM/DD (posix) YYYY\MM\DD (win)

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         make lots of noise [default]
  -q, --quiet           unless errors don't output anything
  -r, --recursive       operate recursively [default]
  -s, --symlink         recurse into symbolic linked directories
  -m, --move            delete original file from SOURCE
  -i, --ignore          ignore photos with no EXIF info
  -d DEPTH, --depth=DEPTH
                        unlimited [default: 0]
  -g LOG, --log=LOG     log all actions [default: stdio]

```