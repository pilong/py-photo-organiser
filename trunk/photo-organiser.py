#!/usr/bin/env python
#Meitham 24 May 2009
__doc__ = """Organise your photos.

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
  -s, --symlink         follow symbolic linked directories
  -m, --move            delete original file from SOURCE
  -d DEPTH, --depth=DEPTH
                        unlimited [default: 0]
  -g LOG, --log=LOG     log all actions [default: sys.stderr]
  -i, --ignore          ignore photos with missing EXIF header [default]
  -p NOEXIFPATH, --process-no-exif=NOEXIFPATH
                        copy/moves images with no EXIF data to [default:
                        undated]
"""
from optparse import OptionParser
from datetime import datetime
import Image
import sys
import os
import shutil
import string
import hashlib
import logging, logging.handlers

__version__ = "0.1"
def getOptions():
    ''' creates the options and return a parser object
    '''
    parser = OptionParser(usage="%prog [options] src dest", version="%prog 0.1")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", 
                      default=True,
                      help="make lots of noise [default]")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose",
                      help="unless errors don't output anything")
    parser.add_option("-r", "--recursive",
                      action="store_true", dest="recursive",
                      help="operate recursively [default]")
    parser.add_option("-s", "--symlink",
                      action="store_true", dest="symlink",
                      help="follow symbolic linked directories")
    parser.add_option("-m", "--move",
                      action="store_true", dest="move",
                      help="delete original file from SOURCE, by default it makes a copy of the file")
    parser.add_option("-d", "--depth",
                      default="0", dest="depth",
                      help="unlimited [default: %default]")
    parser.add_option("-g", "--log",
                      default="sys.stderr", dest="log",
                      help="log all actions [default: %default]")
    parser.add_option("-i", "--ignore",
                      action="store_true", dest="ignore", default=True,
                      help="ignore photos with missing EXIF header [default]")
    parser.add_option("-p", "--process-no-exif",
                      default="undated", dest="noExifPath",
                      help="copy/moves images with no EXIF data to [default: %default]")
    return parser

def getImageDateTime(filepath):
    ''' returns a tuple of YYYY/MM/DD and HH-MM for picture taken date time respectively
    '''
    try:
        im = Image.open(filepath)
        if hasattr(im, '_getexif'):
            exifdata = im._getexif()
            if type(exifdata) == type(None):
                return None, None, None, None
            logging.debug("type of object is %s" %type(exifdata))
            ctime = exifdata[0x9003]
            image_dt_tm = datetime.strptime(ctime, '%Y:%m:%d %H:%M:%S')
            _, ext = os.path.splitext(filepath)
            return image_dt_tm.year, image_dt_tm.month, image_dt_tm.day, \
                datetime.strftime(image_dt_tm, '%H-%M-%S')+ext
        else:
            return None, None, None, None
    except Exception, e:
        print e
        return None, None, None, None
    
def treewalk(top, followlinks=False, depth=0):
    ''' generator similar to os.walk(), but with limited subdirectory depth
    '''
    if not maxdepth is None:
        if  depth > maxdepth:
            return
    for file in os.listdir(top):
        file_path = os.path.join(top, file)
        if os.path.isdir(file_path):
            # its a dir recurse into it
            for dirpath, filename in treewalk(file_path, followlinks, depth+1):
                yield dirpath, filename
        elif os.path.isfile(file_path):
            yield top, file
        else:
            # Unknown file type, print a message
            logging.info('Skipping %s' % pathname)

def isPhoto(path):
    knownPhotoExt = [".jpg",".jpeg",".png"]
    _, ext = os.path.splitext(path)
    if string.lower(ext) in knownPhotoExt:
        return True
    else:
        return False

def isExact(file1, file2):
    ''' checks if two files have exactly same content
    '''
    fold = open(file1) # fold stands for file old - file handler
    fnew = open(file2) # fnew stands for file new - file handler
    hash1 = hashlib.sha256()
    hash2 = hashlib.sha256()
    hash1.update(open(file1).read())
    hash2.update(open(file2).read())
    if hash1.hexdigest() == hash2.hexdigest():
        # files are exact
        logging.info("%s and %s are exact duplicate" %(fullfilepath, newfilepath))
        return True
    else:
        return False
        
def getNewFileName(filepath):
    ''' if file name is not in use return it, otherwise
    returns file name appeneded with _XX where XX is unique in that directory
    '''
    fileinc = 0
    basename, ext = os.path.splitext(filepath)
    while(True):
        fileinc = fileinc + 1
        newname = os.path.join(basename+'_'+str(fileinc), ext)
        if os.path.exists(newname):
            continue
        else:
            return newname
def clone(src, dst, copy=1):
    ''' copy or move file
    '''
    if os.path.exists(dst):
        # check for duplication
        if isExact(src, dts):
            # files are exact
            logger.info("%s and %s are exact duplicate" %(src, dst))
        else:
            # different files with same name, invent a new name
            dst = getNewFileName(dst)
    else:
        # path doesn't even exists, no check for duplication
        dstdir = os.path.dirname(dst)
        if not (os.path.exists(dstdir) and os.path.isdir(dstdir)):
            logger.info("creating dir %s" %dstdir)
            os.makedirs(dstdir)
    if copy:
        shutil.copy(src, dst)
    else:
        shutil.move(src, dst)

    
if __name__=='__main__':
    ''' main
    '''
    parser = getOptions()
    (options, args) = parser.parse_args()

    logger = logging.getLogger('')
    if options.log == "sys.stderr":
        console = logging.StreamHandler()
        logger.addHandler(console)
    else:
        fileHandler = logging.FileHandler(options.log)
        logger.addHandler(fileHandler)
    if len(args) == 1:
        src = dst = args[0]
    elif len(args) == 2:
        src = args[0]
        dst = args[1]
    else:
        logging.error("invalid number of arguments")
        parser.print_help()
        sys.exit()
    if options.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('verbose mode on')
    else:
        logger.debug('verbose mode off')
    if options.symlink:
        logger.debug("following symlinks")
    else:
        logger.debug("ignoring symlinks")
    maxdepth = options.depth
    logger.debug("depth is: "+ options.depth)
    if maxdepth == 0:
        maxdepth = None
    for dirpath, filename in treewalk(top=src, followlinks=options.symlink):
        fullfilepath = os.path.join(dirpath, filename)
        if isPhoto(fullfilepath):
            logger.debug("processing %s" %fullfilepath)
            pYear, pMonth, pDay, pTime = getImageDateTime(fullfilepath)
            if pYear is None:
                logger.warning("%s photo has no known date" %fullfilepath)
                # what to do with photos with missing exif
                if options.ignore:
                    pass
                else:
                    undated = os.path.join(dst, options.noExifPath)
                    clone(fullfilepath, os.path.join(undated, filename), options.move)
            else:
                # photo has a date
                logger.debug("joining %s %d %d %d %s" %(dst, pYear, pMonth, pDay, pTime))
                newfiledir = os.path.join(dst, str(pYear), str(pMonth), str(pDay))
                newfilepath = os.path.join(newfiledir, pTime)
                clone(fullfilepath, newfilepath, options.move)
                        
