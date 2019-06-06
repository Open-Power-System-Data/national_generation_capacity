import hashlib
import os.path
import urllib.parse
import urllib.request
import zipfile
import logging



logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d %b %Y %H:%M:%S'
)

logger = logging.getLogger()

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

        if zipfile.is_zipfile(filepath):
            logger.info('Extracting %s into the directory %s', filename, folderpath)
            with zipfile.ZipFile(filepath, "r") as O:
                O.extractall(folderpath)
            
            return folderpath
    else:
        if zipfile.is_zipfile(filepath):
            logger.info('Using extracted zip files from %s', folderpath)
            return folderpath
        else:
            logger.info('Using local file from %s', filepath)
            return filepath
    



def checkIfEmptyAndSetDefault(df, technology, default=0):
    sub_df = df.loc[df['technology'] == technology, 'capacity']
    
    if len(sub_df) == 0:
        return default
    else:
        return sub_df.values[0]