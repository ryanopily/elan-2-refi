from xml.etree import ElementTree
import uuid
import os

from pympi.Elan import Eaf

from refi_common import parentFolder, stripPath, mkdirs
from annotate import annotate

# Code refractored from original implementation to use PYMPI
# Credit and thanks to Elizabeth!

def convert(elan_file, pfsx_file):

    elan = Eaf(file_path=elan_file)
    elan.file_path = elan_file
    elan.file_name, extension = stripPath(elan.file_path)
    elan.pfsx_path = pfsx_file

    Project = ElementTree.Element('Project')
    node_graph = {'Project': Project}

    parse_annotation_doc(elan, node_graph)
    transfer_codes(elan, node_graph)
    parse_annotations(elan, node_graph)

    Project.append(node_graph['Users'])
    Project.append(node_graph['CodeBook'])
    Project.append(node_graph['Sources'])

    result = ElementTree.ElementTree(Project)
    # Indent only works in the latest python version
    # ElementTree.indent(result, space="\t", level=0)
    return result

def parse_annotation_doc(elan, node_graph):

  Project = node_graph['Project']
  name = elan.file_name

  # Specify the QDA-REFI XML Schema, and set the project name
  Project.set('xmlns','urn:QDA-XML:project:1.0')
  Project.set('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
  Project.set('name', name)
  Project.set('basePath', parentFolder(elan.file_path))
  Project.set('xsi:schemaLocation','urn:QDA-XML:project:1.0 http://schema.qdasoftware.org/versions/Project/v1.0/Project.xsd')

  # REFI Format specifies a "User" - it allows collaboration of different people on one document, tracking their contributions.
  # REFI requires at least one user to be present.
  def create_user(name):
    User = ElementTree.Element('User',{'guid': str(uuid.uuid4()), 'name': name})
    return User

  Users = ElementTree.Element('Users')
  node_graph['Users'] = Users;

  author = elan.adocument['AUTHOR']
  Users.append(create_user("Elan2Refi"))
  Users.append(create_user(author))

def transfer_codes(elan, node_graph):

    # REFI Format specifies a "Code" - think of it as a tier.
    # REFI also specifies a "CodeBook" - this is where all the tiers are defined.
    CodeBook = ElementTree.Element('CodeBook')
    Codes = ElementTree.Element('Codes')
    CodeBook.append(Codes)

    node_graph['CodeBook'] = CodeBook
    node_graph['__codings__'] = {}
    tiers = [tier for tier in elan.get_tier_names() if 'PARENT_REF' not in elan.get_parameters_for_tier(tier).keys()]

    for tier in tiers:

        # Creates a code to be added to the Codebook.
        # It also saves the UUID of the code for later.
        def create_tier(tier_name):
            guid = str(uuid.uuid4())
            node_graph['__codings__'][tier_name] = guid
            Code = ElementTree.Element('Code', {'guid': guid, 'name': tier_name, 'isCodable':'true'})
            return Code

        # We create two of the same codes specifically for ATLAS.ti
        # ATLAS.ti supports "Code groups", which is NOT specified in the REFI-QDA specification - this is their workaround.
        Parent = create_tier(tier)
        Independent = create_tier(tier)
        Codes.append(Parent)
        Parent.append(Independent)

        for child in elan.get_child_tiers_for(tier):
            Child = create_tier(child)
            Parent.append(Child)

    # for cv in elan.get_controlled_vocabulary_names():
    #     Category = ElementTree.Element('Code', {'guid': str(uuid.uuid4()), 'name': cv, 'isCodable': 'true'})
    #     Codes.append(Category)

    #     for cve_id, description in elan.get_cv_entries(cv).items():
    #         Code = ElementTree.Element('Code', {'guid': cve_id[6:], 'name': description[0][0][0], 'isCodable': 'true'})
    #         Category.append(Code)

def parse_annotations(elan, node_graph):
    Sources = ElementTree.Element('Sources')
    node_graph['Sources'] = Sources;

    # Only one transcript per ELAN project?
    Transcript = None

    for media in elan.media_descriptors:
        mime = media['MIME_TYPE']
        source_path = 'relative:///' + media['RELATIVE_MEDIA_URL'][2:]

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

            # REFI Format specifies "quotations" - think of them as annotations.
            # There are different types of quotations - VideoSelection, etc.
            selection = ElementTree.Element('VideoSelection', {'guid': annotation[4], 'begin': begin, 'end': end, 'name': value})

            # This assigns a code to the quotation
            Coding = ElementTree.Element('Coding', {'guid': str(uuid.uuid4())})
            CodeRef = ElementTree.Element('CodeRef', {'targetGUID': node_graph['__codings__'][tier_name]})

            VideoSource.append(selection)
            selection.append(Coding)
            Coding.append(CodeRef)

    for tier_name, reference_dict in references.items():
        for reference_id, reference in reference_dict.items():
            annotation_id = reference[0]
            value = reference[1]

            for tier_name, annotation_dict in annotations.items():
                if annotation_id in annotation_dict:
                    begin = str(timeslots[annotation_dict[annotation_id][0]])
                    end   = str(timeslots[annotation_dict[annotation_id][1]])

            selection = ElementTree.Element('VideoSelection',{'guid':str(uuid.uuid4()),'begin':begin,'end':end,'name':value})
            Coding = ElementTree.Element('Coding', {'guid': str(uuid.uuid4())})
            CodeRef = ElementTree.Element('CodeRef', {'targetGUID': node_graph['__codings__'][tier_name]})

            VideoSource.append(selection)
            selection.append(Coding)
            Coding.append(CodeRef)
