import os.path
import logging

# sets up the logger config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d %b %Y %H:%M:%S'
)

#init a logger
logger = logging.getLogger()

# create output directories if they do not exist
os.makedirs('output', exist_ok=True)
os.makedirs(os.path.join('output'), exist_ok=True)
os.makedirs(os.path.join('output', 'original_data'), exist_ok=True)

