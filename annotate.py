import uuid
import shutil

from xml.etree import ElementTree
from pympi.Elan import Eaf

def annotate(elan, transcript_file):

    with open(transcript_file, 'w') as a:
        a.write('')

    with open(transcript_file, 'a+') as transcript:

        TS = {}
        Transcript = ElementTree.Element('Transcript', {'guid': str(uuid.uuid4())})

        for tier in get_transcript_tiers(elan.pfsx_path):
            TS.update(elan.tiers[tier][0])

        if len(TS) == 0:
            # This allows a user to select which tiers to include in the generated transcript
            # We latch on to ELAN's psfx file to do this
            raise Exception("No transcript tiers found! Export a 'Traditional Transcript Text' from ELAN to proceed.")

        # Sort TS by timeslots to get annotations in order
        timeslots = elan.timeslots
        TS = sorted(TS.items(), key = lambda kv: timeslots[kv[1][0]])

        # Tier = tuple(timeslotID start, timeslotID end, transcript text)
        for annotation in TS:
            annotation = annotation[1]
            timestamp = timeslots[annotation[0]]

            # SyncPoint syncs the VideoSource with the transcript text.
            # As the video plays, different transcript text is selected.
            Sync = ElementTree.Element('SyncPoint', {'guid': str(uuid.uuid4()), 'position': str(transcript.tell()), 'timeStamp': str(timestamp)})
            transcript.write(annotation[2] + '\n')
            Transcript.append(Sync)

        return Transcript

def get_transcript_tiers(pfsx_file):

    transcript_tiers = []

    # Read pfsx file in as an XML element
    for prefList in ElementTree.parse(pfsx_file).getroot().iter('prefList'):
        key = prefList.get('key')

        if(key == 'ExportTradTranscript.selectedTiers'):
            for tier in prefList.iter('String'):
                transcript_tiers.append(tier.text)

    return transcript_tiers
