import os

""" Gets parent directory of a file """
def parentFolder(file):
    parent = os.path.join(file, os.pardir)
    return os.path.abspath(parent)
    
""" Gets filename and extension """
def stripPath(path):
    basename = os.path.basename(path)
    return os.path.splitext(basename)
    
""" Create folder and parent directories if they don't exist"""
def mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path)