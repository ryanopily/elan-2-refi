from xml.etree import ElementTree
import uuid
import os

from pympi.Elan import Eaf

from refi_common import parentFolder, stripPath, mkdirs
from annotate import annotate

# Code refractored from Elizabeth's original implementation to use PYMPI, to make the code more readable

def convert(elan_file, pfsx_file):

    # See pympi-ling for documentation
    elan = Eaf(file_path=elan_file)
    elan.file_path = elan_file
    elan.pfsx_path = pfsx_file
    elan.file_name, extension = stripPath(elan.file_path)

    Project = ElementTree.Element('Project')
    
    # Dictionary containing the root Project node and all child elements
    node_graph = {}
    node_graph['Project'] = Project
    
    # Convert from ELAN to REFI functions
    parse_annotation_doc(elan, node_graph)
    transfer_codes(elan, node_graph)
    parse_annotations(elan, node_graph)
    
    # Link child nodes to root Project node
    Project.append(node_graph['Users'])
    Project.append(node_graph['CodeBook'])
    Project.append(node_graph['Sources'])
    
    result = ElementTree.ElementTree(Project)
    # ElementTree.indent(result, space="\t", level=0)
    
    return result
    
def parse_annotation_doc(elan, node_graph):

  Project = node_graph['Project']
  name = elan.file_name

  #specify the project name and the refi xml schema
  Project.set('xmlns','urn:QDA-XML:project:1.0')
  Project.set('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
  Project.set('name', name)
  Project.set('basePath', parentFolder(elan.file_path))
  Project.set('xsi:schemaLocation','urn:QDA-XML:project:1.0 http://schema.qdasoftware.org/versions/Project/v1.0/Project.xsd')
  
  def create_user(name):
    User = ElementTree.Element('User',{'guid': str(uuid.uuid4()), 'name': name})
    return User
    
  Users = ElementTree.Element('Users')
  node_graph['Users'] = Users;
  
  author = elan.adocument['AUTHOR']
  
  Users.append(create_user("Elan2Refi"))
  Users.append(create_user(author))
  
def transfer_codes(elan, node_graph):
    
    CodeBook = ElementTree.Element('CodeBook')
    node_graph['CodeBook'] = CodeBook
    node_graph['__codings__'] = {}
    
    Codes = ElementTree.Element('Codes')    
    for tier in elan.get_tier_names():
        node_graph['__codings__'][tier] = str(uuid.uuid4())
        Code = ElementTree.Element('Code', {'guid': node_graph['__codings__'][tier], 'name': tier, 'isCodable':'true'})
        Codes.append(Code)
        
    CodeBook.append(Codes)

def parse_annotations(elan, node_graph):
    Sources = ElementTree.Element('Sources')
    node_graph['Sources'] = Sources;
    
    for media in elan.media_descriptors:
       
        mime = media['MIME_TYPE']
        source_path = 'relative:///' + media['RELATIVE_MEDIA_URL'][2:]
       
        Transcript = None

        if mime == "video/mp4":
            VideoSource = ElementTree.Element('VideoSource',{'guid':str(uuid.uuid4()),'path':source_path})

            if Transcript == None:
                transcript_path = elan.file_name + "_transcript.txt"
                Transcript = annotate(elan, transcript_path)
                Transcript.set('plainTextPath', 'internal://' + transcript_path)

            VideoSource.append(Transcript)
            Sources.append(VideoSource)

            add_video_selections(elan, VideoSource, node_graph['Project'], node_graph)
            
        if mime == 'audio/x-wav':
            AudioSource = ElementTree.Element('AudioSource', {'guid': str(uuid.uuid4()), 'path': source_path})
            Sources.append(AudioSource)
  
# This section of code works best without using pympi
def add_video_selections(elan, VideoSource, refi_root, node_graph):

    annotations = {}
    references = {}
    timeslots = elan.timeslots

    for tier_name, tier in elan.tiers.items():

        annotations[tier_name] = {}
        references[tier_name] = {}

        for aligned_id, aligned in tier[0].items():
            annotations[tier_name][aligned_id] = aligned

        for reference_id, reference in tier[1].items():
            references[tier_name][reference_id] = reference

    for tier_name, annotation_dict in annotations.items():
        for annotation_id, annotation in annotation_dict.items():
            begin = str(timeslots[annotation[0]])
            end   = str(timeslots[annotation[1]])
            value = str(annotation[2])

            annotation += (str(uuid.uuid4()),)

            selection = ElementTree.Element('VideoSelection', {'guid': annotation[4], 'begin': begin, 'end': end, 'name': value})
            VideoSource.append(selection)

    for tier_name, reference_dict in references.items():
        for reference_id, reference in reference_dict.items():
            annotation_id = reference[0]
            value = reference[1]

            for tier_name, annotation_dict in annotations.items():
                if annotation_id in annotation_dict:
                    begin = annotation_dict[annotation_id][0]
                    end   = annotation_dict[annotation_id][1]

            selection = ElementTree.Element('VideoSelection',{'guid':str(uuid.uuid4()),'begin':begin,'end':end,'name':value})
            VideoSource.append(selection)