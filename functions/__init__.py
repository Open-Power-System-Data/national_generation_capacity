import os.path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d %b %Y %H:%M:%S'
)

logger = logging.getLogger()

os.makedirs('output', exist_ok=True)
os.makedirs(os.path.join('output'), exist_ok=True)
os.makedirs(os.path.join('output', 'original_data'), exist_ok=True)

