import os
import shutil
import argparse

import pympi
from zipfile import ZipFile

import elan_to_refi
from refi_common import parentFolder, stripPath, mkdirs
  
def invoke(projectDir, outputFile):
    
    elan_name = None
    elan_file = None
    pfsx_file = None
    video_files = []
    audio_files = []

    project_files = os.listdir(projectDir) 
    os.chdir(projectDir)

    # Search for project files
    for file in project_files:

        if os.path.isfile(file):
            name, extension = os.path.splitext(file)
            
            if extension == '.eaf':
                elan_file = file
                elan_name = name

            elif extension == '.pfsx':
                pfsx_file = file

           
    if elan_file is None:
        raise Exception(f"No ELAN (EAF) project file found!\n Found: {project_files}")

    # The PFSX file is needed to get tiers to include in the generated transcript 
    if pfsx_file is None:
        raise Exception(f"No ELAN (PFSX) preferences file found!\n Found: {project_files}")

    elan_project = pympi.Elan.Eaf(elan_file)
    # XML Element Tree representing QDPX (QDE) Project file
    qde_tree = elan_to_refi.convert(elan_file, pfsx_file)

    # Search for media files
    for media in elan_project.media_descriptors:
        
        mime = media['MIME_TYPE']
        
        def collect_media(media, target):
            absolute = media['MEDIA_URL']
            relative = media['RELATIVE_MEDIA_URL']
           
            if os.path.exists(absolute):
                target.append(absolute)
            
            elif os.path.exists(relative):
                target.append(relative)
                
            else:
                raise Exception(f"Media file {absolute} or {relative} couldn't be found!")           
        
        if mime == 'audio/x-wav':
            collect_media(media, audio_files)
        
        if mime == 'video/mp4':     
            collect_media(media, video_files)

    # outputFile will be named after the elan project and placed in the same directory as it by default
    if outputFile is None:
        outputName, extension = stripPath(elan_file)
        outputFile = os.path.join(os.getcwd(), outputName + '.qdpx')

    # Build folder to compress into QDPX archive
    archive_target = 'elan2refi'
    sources_file = os.path.join(archive_target, 'sources')
    mkdirs(sources_file)
    transcript_file = elan_name + '_transcript.txt'
    shutil.copyfile(transcript_file, os.path.join(sources_file, transcript_file)) 
    os.chdir(archive_target)
    qde_file = 'project.qde'
    qde_tree.write(qde_file,encoding='utf-8',xml_declaration=True)

    with ZipFile(outputFile, 'w') as archive:
        archive.write(qde_file)

        for file in os.listdir('sources'):
            file = os.path.join('sources', file)
            archive.write(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', metavar='file', type=str, default=os.getcwd(), help='EAF project file OR directory')
    parser.add_argument('-o', metavar='output', type=str, default=None, help='Path of qdpx output file')

    args = parser.parse_args()
    projectDir = parentFolder(args.f) if os.path.isfile(args.f) else args.f
    
    invoke(projectDir, args.o)