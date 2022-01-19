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
    
    def get_vocab():
        result = {}
        cvs = elan.controlled_vocabularies
        for id in cvs:
            cv = cvs[id][1:-1]
            
            for cve in cv:
                for id2 in cve:
                    value = cve[id2][0][0][0]
                    result[id2] = value
                    
        return result
    
    CodeBook = ElementTree.Element('CodeBook')
    node_graph['CodeBook'] = CodeBook
    
    Codes = ElementTree.Element('Codes')
    vocab = get_vocab()
                    
    for code in vocab.keys():
        Code = ElementTree.Element('Code', {'guid': code[6:], 'name': vocab[code], 'isCodable':'true'})
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

            add_video_selections(elan, VideoSource, node_graph['Project'])
            
        if mime == 'audio/x-wav':
            AudioSource = ElementTree.Element('AudioSource', {'guid': str(uuid.uuid4()), 'path': source_path})
            Sources.append(AudioSource)
  
# This section of code works best without using pympi
def add_video_selections(elan, VideoSource, refi_root):
    elan_root = ElementTree.parse(elan.file_path).getroot()
    
    timeslots = elan.timeslots
    timeslots = dict(sorted(timeslots.items(), key = lambda kv: kv[1]))
    
    for annot in elan_root.iter('ALIGNABLE_ANNOTATION'):
        id = annot.attrib['ANNOTATION_ID']
        guid = str(uuid.uuid4())
        begin = str(timeslots[annot.attrib['TIME_SLOT_REF1']])
        end = str(timeslots[annot.attrib['TIME_SLOT_REF2']])
        val = annot.find('ANNOTATION_VALUE').text
        if val == None:
          val = ''
       
        #store these attributes in refi format
        ref_elem = ElementTree.Element('VideoSelection',{'guid':guid,'begin':begin,'end':end,'name':val})
        VideoSource.append(ref_elem)

        #if annotation has cv reference, add code as child of selection
        if 'CVE_REF' in annot.attrib.keys():
          cv = annot.attrib['CVE_REF']
          Coding = ElementTree.Element('Coding',{'guid':str(uuid.uuid4())})
          ref_elem.append(Coding)
          CodeRef = ElementTree.Element('CodeRef',{'targetGUID':cv[6:]})
          Coding.append(CodeRef)

    #transfer ref annotations
    for annot in elan_root.iter('REF_ANNOTATION'):
        id = annot.attrib['ANNOTATION_ID']
        guid = str(uuid.uuid4())
        val = annot.find('ANNOTATION_VALUE').text
        if val == None:
          val = ''
        cv = annot.attrib.get('CVE_REF','')
    
        #retrieve parent time stamp before adding new selection
        parent_id = annot.attrib['ANNOTATION_REF']
        for nodes in refi_root.findall('VideoSelection'):
            if node.attrib['guid']==id:
                begin = node.attrib['begin']
                end = node.attrib['end']
                break

        #store these attributes in refi format
        ref_elem = ElementTree.Element('VideoSelection',{'guid':guid,'begin':begin,'end':end,'name':val})
        VideoSource.append(ref_elem)

        #if annotation has cv reference, add code as child of selection
        Coding = ElementTree.Element('Coding',{'guid':str(uuid.uuid4())})
        ref_elem.append(Coding)
        CodeRef = ElementTree.Element('CodeRef',{'targetGUID':cv[6:]})
        Coding.append(CodeRef)