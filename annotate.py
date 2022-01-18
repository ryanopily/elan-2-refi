import uuid
import shutil

from xml.etree import ElementTree
from pympi.Elan import Eaf

def annotate(elan, transcript_file):

    # Overwrite previous files, since we're appending
    with open(transcript_file, 'w') as a:
        a.write('')
    
    # Write new transcript file - this helps link the text to file position
    with open(transcript_file, 'a+') as transcript:
    
        # Sort by timestamps - helps us order annotations
        timeslots = elan.timeslots

        TS = []
        elan_root = ElementTree.parse(elan.file_path).getroot()

        for annot in elan_root.iter('ALIGNABLE_ANNOTATION'):
            begin = timeslots[annot.attrib['TIME_SLOT_REF1']]
            val = annot.find('ANNOTATION_VALUE').text
            
            if val == None:
              val = ''

            #if annotation has cv reference, add code as child of selection
            if 'CVE_REF' not in annot.attrib.keys():
                TS.append((begin, val))

        TS = sorted(TS, key = lambda kv: kv[0])
         
        Transcript = ElementTree.Element('Transcript', {'guid': str(uuid.uuid4())})

		# Tier = tuple(timeslotID start, timeslotID end, transcript text)
        for annotation in TS:

            text = annotation[1]
            timestamp = annotation[0]

            # print(annotation)
            # print(f"SYNC time = {timestamp} position = {transcript.tell()} TEXT={text}")

            Sync = ElementTree.Element('SyncPoint', {'guid': str(uuid.uuid4()), 'position': str(transcript.tell()), 'timeStamp': str(timestamp)})
            transcript.write(text + '\n')
            
            Transcript.append(Sync)

        return Transcript
            
            
