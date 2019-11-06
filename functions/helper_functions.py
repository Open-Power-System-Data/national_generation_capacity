import hashlib
import os.path
import urllib.parse
import urllib.request
import zipfile
import shutil
from . import logger


def get_sha_hash(path, blocksize=65536):
    sha_hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        buffer = f.read(blocksize)
        while len(buffer) > 0:
            sha_hasher.update(buffer)
            buffer = f.read(blocksize)
        return sha_hasher.hexdigest()
    
 
def createDownloadFolderPath(source):
    folderpath = os.path.join('download', source)
    
    return folderpath

def isZipAndNotExcel(filepath):
    """
    Returns false if the file is an Excel file. Return true if file is a zipped.
    Parameters
    ----------
    filepath : str
        Path to the file
    """
    
    if (os.path.splitext(filepath)[1] in [".xlsx", ".xls"] or not
    zipfile.is_zipfile(filepath)):
        
        return False
    
    else:
        return True
    
        
    
def downloadandcache(url, filename, source):
    """
    Download a file into a folder called "downloads".
    Returns the local filepath.

    Parameters
    ----------
    url : str
        Url of a file to be downloaded
    filename : str
        Name of the downloaded file
    source : str
        Source of the downloaded file
    """

    folderpath = createDownloadFolderPath(source)
    filepath = os.path.join(folderpath, filename)    

    # check if file exists, otherwise download it
    if not os.path.exists(filepath):
        os.makedirs(folderpath, exist_ok=True)
        logger.info('Downloading file %s', filename)
        urllib.request.urlretrieve(url, filepath)

        # extract files if they are zipped
        if isZipAndNotExcel(filepath):
            logger.info('Extracting %s into the directory %s', filename, folderpath)
            with zipfile.ZipFile(filepath, "r") as O:
                O.extractall(folderpath)
            
            return folderpath
        else:
            return filepath
        
    else:
        if isZipAndNotExcel(filepath):
            logger.info('Using extracted zip files from %s', folderpath)
            return folderpath
        else:
            logger.info('Using local file from %s', filepath)
            return filepath
    

def unstackData(df):
    
    pt = df.pivot_table(values='capacity',
                        index=['country','year'],
                        columns='technology')
    
    return pt

def restackData(df):
    return df.stack().reset_index().rename(columns={0: 'capacity'})

def checkIfEmptyAndSetDefault(df, technology, default=0):
    sub_df = df.loc[df['technology'] == technology, 'capacity']
    
    if len(sub_df) == 0:
        return default
    else:
        return sub_df.values[0]


def copydir(source, dest):
    """Copy a directory structure overwriting existing files"""
    for root, dirs, files in os.walk(source):
        if not os.path.isdir(root):
            os.makedirs(root)

        for file in files:
            rel_path = root.replace(source, '').lstrip(os.sep)
            dest_path = os.path.join(dest, rel_path)

            if not os.path.isdir(dest_path):
                os.makedirs(dest_path)

            shutil.copyfile(os.path.join(root, file), os.path.join(dest_path, file))

def make_archive(source, destination):
        base = os.path.basename(destination)
        name = base.split('.')[0]
        format = base.split('.')[1]
        archive_from = os.path.dirname(source)
        archive_to = os.path.basename(source.strip(os.sep))
        print(source, destination, archive_from, archive_to)
        shutil.make_archive(name, format, archive_from, archive_to)
        filename = '%s.%s'%(name,format)
        shutil.move(filename, destination)
        print("Zipped " + name + " to " + filename)