import os
import shutil
import argparse

from zipfile import ZipFile

import pympi
import elan_to_refi

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
  
def invoke(projectDir, outputName):
        
    elan_file = None
    video_file = None
    transcript_file = None
           
    qdpx_output = os.getcwd()

    files = os.listdir(projectDir) 
    os.chdir(projectDir)

    # Search for ELAN and Transcription file
    for file in files:
        if os.path.isfile(file):
            name, extension = os.path.splitext(file)
            
            if extension == '.eaf':
                elan_file = file
            elif extension == '.txt':
                transcript_file = file
        
    if elan_file is None:
        raise Exception(f"No ELAN (EAF) project file found!\n Found: {files}")
        
    if transcript_file is None:
        raise Exception(f"No transcript file found!\n Found: {files}")

    project = pympi.Elan.Eaf(elan_file)

    # Search for video file
    for media in project.media_descriptors:
        
        mime = media['MIME_TYPE']
        if mime == 'video/mp4':
                   
            absolute = media['MEDIA_URL']
            relative = media['RELATIVE_MEDIA_URL']
           
            if os.path.exists(absolute):
                video_file = absolute
            
            elif os.path.exists(relative):
                video_file = relative
                
            else:
                raise Exception(f"Media file {absolute} or {relative} couldn't be found!")

    QDE = elan_to_refi.convert(elan_file, transcript_file)

    # Create folder for QDPX file
    parent = 'elan2refi'
    qde_file = 'project.qde'
    sources_file = os.path.join(parent, 'sources')
    mkdirs(sources_file)

    shutil.copy(video_file, sources_file)
    shutil.copyfile(transcript_file + ".e2q", os.path.join(sources_file, transcript_file)) 
    
    os.chdir(parent)
    QDE.write(qde_file,encoding='utf-8',xml_declaration=True)
        
    if outputName is None:
        outputName, extension = stripPath(elan_file)
        
    extension = '.qdpx'

    with ZipFile(os.path.join(qdpx_output, outputName + extension), 'w') as archive:
        archive.write(qde_file)
        sources_file = 'sources'

        for file in os.listdir(sources_file):
            file = os.path.join(sources_file, file)
            archive.write(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', metavar='file', type=str, default=os.getcwd(), help='ELAN (EAF) project file OR directory')
    parser.add_argument('-o', metavar='output', type=str, default=None, help='Name of output file (QDPX)')

    args = parser.parse_args()
    projectDir = parentFolder(args.f) if os.path.isfile(args.f) else args.f
    
    invoke(projectDir, args.o)