#!/usr/bin/env python
#Meitham 27 June 2009
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

__version__ = "0.101"

class ImageException(Exception):
    pass

class InvalidImageFile(ImageException):
    pass

class InvalidDateTag(ImageException):
    pass

class MissingDateTag(ImageException):
    pass

class MissingImageFile(ImageException):
    pass
    
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
    hash1 = hashlib.sha256()
    hash2 = hashlib.sha256()
    hash1.update(open(file1).read())
    hash2.update(open(file2).read())
    if hash1.hexdigest() == hash2.hexdigest():
        # files are exact
        logging.info("%s and %s are exact duplicate" %(file1, file2))
        return True
    else:
        return False


class ImageDate:
    ''' a date and time class
    '''
    def __init__(self, img_dt_tm=None):
        ''' creates an instance using the given file img_dt_tm
        '''
        if type(img_dt_tm) == type(None):
            raise InvalidDateTag('missing date/time stamp')
        try:
            if type(img_dt_tm) == type(''): # string
                self.img_dt_tm = datetime.strptime(img_dt_tm, '%Y:%m:%d %H:%M:%S')
                # self.img_dt_tm.microsecond = 0
        except ValueError, e:
            raise InvalidDateTag('missing date/time stamp')

    def getPath(self, base, filename):
        ''' returns a string that describes a path as a date such as
        year/month/day/hour_minute_second_microsecond.
        '''
        _, fileExt = os.path.splitext(filename.lower())
        fileName = self.img_dt_tm.strftime('%Y_%m_%d-%H_%M_%S_%f') + fileExt
        return os.path.join(base, \
                            str(self.img_dt_tm.year),
                            str(self.img_dt_tm.month),
                            str(self.img_dt_tm.day), fileName)

    def __str__(self):
        return str(self.img_dt_tm)

    def incMicrosecond(self):
        self.img_dt_tm.microsecond += timedelta(microsecond=1)

class ImageFile:
    ''' a file that contains valid image format
    '''
    def __init__(self, fullfilepath):
        ''' creates an instance of the ImageFile
        '''
        if not os.path.exists(fullfilepath): # file missing
            raise MissingImageFile('file not found %s' %fullfilepath)
        try:
            im = Image.open(fullfilepath)
            self.srcfilepath = fullfilepath
        except IOError, e:
            raise InvalidImageFile('invalid image file %s' %fullfilepath)
        if not hasattr(im, '_getexif'):
            raise MissingDateTag('image file has no date %s' %fullfilepath)
        else:
            try:
                exifdata = im._getexif()
            except KeyError, e:
                self.imagedate = None
                logging.debug(e)
                raise MissingDateTag('image file has no date %s' %fullfilepath)
            logging.debug("type of object is %s" %type(exifdata))
            if type(exifdata) == type(None):
                raise InvalidDateTag('exif date of type None')
            try:
                ctime = exifdata[0x9003]
                self.imagedate = ImageDate(ctime)
            except InvalidDateTag, e:
                self.imagedate = None
                logging.debug(e)
            except KeyError, e:
                self.imagedate = None
                logging.debug(e)
    
    def getFileName(self, base):
        ''' gets a proper name and path with no duplications
        '''
        if self.imagedate is None:
            # i should handle images with no date here
            logger.info("no image date for file %s " %self.srcfilepath)
            return None
        while True:
            self.dstfilename = self.imagedate.getPath(base, self.srcfilepath)
            if os.path.exists(self.dstfilename):
                logger.info("image already exists %s " %self.dstfilename)
                if isExact(self.srcfilepath, self.dstfilename):
                    logger.info("and its duplicate %s " %self.dstfilename)
                    return None # duplicate
                else:
                    logger.info("but not duplicate %s " %self.dstfilename)
                    self.imagedate.incMicrosecond()
            else:
                return self.dstfilename
    
    def move(self, base, deleteOriginal=None):
        if self.getFileName(base) is None:
            logger.info("unknown destination for %s " %self.srcfilepath)
            return
        dstdir = os.path.dirname(self.dstfilename)
        if not (os.path.exists(dstdir) and os.path.isdir(dstdir)):
            logger.info("creating dir %s" %dstdir)
            os.makedirs(dstdir)
        if deleteOriginal:
            logger.info("moving %s ==> %s " %(self.srcfilepath, self.dstfilename))
            shutil.move(self.srcfilepath, self.dstfilename)
        else:
            logger.info("copying %s ==> %s " %(self.srcfilepath, self.dstfilename))
            shutil.copy(self.srcfilepath, self.dstfilename)

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

class FilesTree:
    def __init__(self):
        pass
    
    def __next__(self):
        pass
    
    def __iter__(self):
        pass
    
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
        # this needs to build the tree under temp and move it to dest when done
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
        logger.debug("processing %s" %fullfilepath)
        if not isPhoto(fullfilepath): # ignore non image extensions
            logger.debug("ignoring non image file %s" %fullfilepath)
            continue
        try:
            imagefile = ImageFile(fullfilepath)
        except ImageException, e:
            logger.debug(e)
            continue
        imagefile.move(dst, options.move)