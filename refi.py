import os
import shutil
import argparse

from zipfile import ZipFile

from refi_common import parentFolder, stripPath, mkdirs

import pympi
import elan_to_refi
  
def invoke(projectDir, outputName):
        
    elan_name = None
    elan_file = None
    video_files = []
    audio_files = []
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
                elan_name = name
                break
        
    if elan_file is None:
        raise Exception(f"No ELAN (EAF) project file found!\n Found: {files}")

    QDE = elan_to_refi.convert(elan_file)
    project = pympi.Elan.Eaf(elan_file)

    transcript_file = name + "_transcript.txt"


    # Search for video file
    for media in project.media_descriptors:
        
        mime = media['MIME_TYPE']
        
        def collect_media(target):
            absolute = media['MEDIA_URL']
            relative = media['RELATIVE_MEDIA_URL']
           
            if os.path.exists(absolute):
                target.append(absolute)
            
            elif os.path.exists(relative):
                target.append(relative)
                
            else:
                raise Exception(f"Media file {absolute} or {relative} couldn't be found!")           
        
        if mime == 'audio/x-wav':
            collect_media(audio_files)
        
        if mime == 'video/mp4':     
            collect_media(video_files)

    # Create folder for QDPX file
    parent = 'elan2refi'
    qde_file = 'project.qde'

    sources_file = os.path.join(parent, 'sources')
    mkdirs(sources_file)

    shutil.copyfile(transcript_file, os.path.join(sources_file, transcript_file)) 
    
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