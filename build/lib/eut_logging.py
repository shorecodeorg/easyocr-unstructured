#kevin fink
#kevin@shorecode.org
#Wed Dec  4 01:42:15 PM +07 2024

#.py

import logging
import traceback
import platform
import os
import sys

class CustomLogger(logging.Logger):
    def __init__(self, name):
        super().__init__(name)
    
    def trace(self, e):
        self.error(f'E: {e}, TB: {traceback.format_exc()}')        

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.ERROR):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())
    def flush(self):
        pass

dev = False

def set_logging(name: str, filename: str) -> logging.Logger:
    """
    Creates a logging directory if one does not exist and initializes and configures a logger
    
    Args:
    name (str) : Name of the logger
    filename (str) : Name of the file to output the log to
    
    Returns:
    logging.Logger: Logger object
    """
    # Checks for a logging directory and creates one if it does not exist
    logging_dir = os.path.join(os.path.dirname(__file__), 'logging')
    if not os.path.isdir(logging_dir):
        os.mkdir(logging_dir)
                
    # Delete the logging file if it is greater than 10Mb
    try:
        # Get the size of the logging file
        file_size = os.path.getsize(filename)
        
        if file_size > 10000000:
            os.remove(filename)
            with open(filename, 'w', encoding='utf-8') as fn:
                fn.write('New log')  
    except (PermissionError, FileNotFoundError):
        pass 

    # Setup logging configuration
    logging.basicConfig(filename=filename, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

    # Create a logger
    logger = CustomLogger(name)

    if dev is True:        
        # Create a file handler
        console_handle = logging.StreamHandler()
    
        # Add the file handler to the logger
        logger.addHandler(console_handle)

    else:        
        sys.stderr = StreamToLogger(logger,logging.ERROR)
    
    return logger

