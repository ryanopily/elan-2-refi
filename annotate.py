import uuid
import shutil

from xml.etree import ElementTree
from pympi.Elan import Eaf

def annotate(elan, transcript_file):

    # Overwrite previous files, so we can use append mode.
    with open(transcript_file, 'w') as a:
        a.write('')
    
    # Write new transcript file - this helps link the text to file position
    with open(transcript_file, 'a+') as transcript:

        TS = {}
        Transcript = ElementTree.Element('Transcript', {'guid': str(uuid.uuid4())})

        # Populate TS with transcript tiers
        for tier in get_transcript_tiers(elan.pfsx_path):
            TS.update(elan.tiers[tier][0])

        if len(TS) == 0:
            raise Exception("No transcript tiers found! Export a 'Traditional Transcript Text' from ELAN to proceed.")

        # Sort TS by timeslots to get annotations in order
        timeslots = elan.timeslots
        TS = sorted(TS.items(), key = lambda kv: timeslots[kv[1][0]])

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

# Attempts to find a 'prefList' of tiers that are included in an exported transcript
def get_transcript_tiers(pfsx_file):

    transcript_tiers = []

    # Iterate through all 'prefList' nodes
    for prefList in ElementTree.parse(pfsx_file).getroot().iter('prefList'):
        
        key = prefList.get('key')

        if(key == 'ExportTradTranscript.selectedTiers'): 

            # Iterate though the list to get the transcript tiers
            for tier in prefList.iter('String'):
                transcript_tiers.append(tier.text)

    return transcript_tiers