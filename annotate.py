import uuid
import shutil

from xml.etree import ElementTree
from pympi.Elan import Eaf

def annotate(elan_file, transcript_file):
    elan = Eaf(file_path=elan_file)
    
    transcript_file += ".e2q"
    
    # Overwrite previous files, since we're appending
    with open(transcript_file, 'w') as a:
        a.write('')
    
    # Write new transcript file - this helps link the text to file position
    with open(transcript_file, 'a+') as transcript:
        TS = elan.tiers['TS-Contribution'][0]
        AS = elan.tiers['AS-Contribution'][0]
        
        # Sort by timestamps - helps us order annotations
        timeslots = elan.timeslots
        timeslots = dict(sorted(timeslots.items(), key = lambda kv: kv[1]))

        TS.update(AS)
        TS = sorted(TS.items(), key = lambda kv: timeslots[kv[1][0]])
         
        Transcript = ElementTree.Element('Transcript', {'guid': str(uuid.uuid4())})
        
		# Tier = tuple(timeslotID start, timeslotID end, transcript text)
        for annotation in TS:
        
            annotation = annotation[1]
            timestamp = timeslots[annotation[0]]

            # print(annotation)
            # print(f"SYNC time = {timestamp} position = {transcript.tell()}")

            Sync = ElementTree.Element('SyncPoint', {'guid': str(uuid.uuid4()), 'position': str(transcript.tell()), 'timeStamp': str(timestamp)})
            transcript.write(annotation[2] + '\n')
            
            Transcript.append(Sync)
        
        return Transcript
