import flywheel
import json
import os
import re


def load_config(file_path: str) -> dict:
    """Load the JSON configuration file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Error reading config file: {e}")


def initialize_flywheel_client(config: dict) -> flywheel.Client:
    """Initialize the Flywheel client using the API key from the config."""
    try:
        api_key = config['inputs']['api-key']['key']
        return flywheel.Client(api_key=api_key)
    except KeyError:
        raise RuntimeError("API key not found in the configuration file.")


def match_modality(file_name: str) -> str:
    """
    Determine which QC modality (if any) a file name matches, using the
    same rules as the per-file QC dispatch below.

    Args:
        file_name: Name of the file to check.

    Returns:
        The modality name ('T2w', 'T1w', 'FLAIR', 'ADC') or None if no match.
    """
    if 'T2' in file_name and 'Align' not in file_name and 'Segmentation' not in file_name:
        return 'T2w'
    if 'T1' in file_name:
        return 'T1w'
    if 'FLAIR' in file_name:
        return 'FLAIR'
    if 'ADC' in file_name:
        return 'ADC'
    return None


def normalize_filename(name: str) -> str:
    """
    Strip leading and trailing series-number markers (e.g. '5 - ' prefix,
    '_5' suffix before the extension) from a file name so that repeat
    acquisitions of the same scan, run under different series numbers,
    normalize to the same string.

    Args:
        name: File name to normalize.

    Returns:
        The file name with any leading/trailing series-number markers removed.
    """
    name = re.sub(r'^\s*\d+\s*[-_]\s*', '', name)
    name = re.sub(r'_\d+(\.\w+(\.\w+)?)$', r'\1', name)
    return name.strip()


def check_repeat_acquisitions(fw: flywheel.Client, session) -> bool:
    """
    Check whether a session contains repeat acquisitions of the same QC
    modality (e.g. T2 axial acquired more than once under different series
    numbers).

    Args:
        fw: Flywheel client.
        session: Flywheel session object.

    Returns:
        True if the session has 2+ distinct acquisitions producing a nifti
        file that matches the same modality and normalized file name.
    """
    acquisitions = fw.acquisitions.find(f'session={session.id}')

    seen = {}
    for acquisition in acquisitions:
        for file_obj in acquisition.files:
            if file_obj.type != 'nifti':
                continue
            modality = match_modality(file_obj.name)
            if modality is None:
                continue
            key = (modality, normalize_filename(file_obj.name))
            seen.setdefault(key, set()).add(acquisition.id)

    return any(len(acq_ids) > 1 for acq_ids in seen.values())


def resolve_session_id(config: dict, input_container) -> str:
    """
    Resolve the session to tag for review.

    Prefers the job's destination container when it's a session (the case
    for a gear job launched directly against a session, with no file
    input). Falls back to the input file's parent session otherwise.

    Args:
        config: Gear run-time config (config.json contents).
        input_container: The input file's acquisition container, or None
            if no file input was provided.

    Returns:
        The session id to tag.
    """
    destination = config.get('destination', {})
    if destination.get('type') == 'session':
        return destination['id']
    if input_container is not None:
        return input_container.parents['session']
    raise RuntimeError(
        "Unable to resolve session: no session destination and no input file provided"
    )


def tag_session_for_review(fw: flywheel.Client, session):
    """
    Tag a session for review by the session-level reader task, flagging
    repeat acquisitions of the same scan type as 'repeat-acq'.

    Args:
        fw: Flywheel client.
        session: Flywheel session object.
    """
    if 'session-read' not in session.tags:
        session.add_tag('session-read')
        print(f"session {session.label}: 'session-read' tag added")

    if check_repeat_acquisitions(fw, session):
        if 'repeat-acq' not in session.tags:
            session.add_tag('repeat-acq')
            print(f"session {session.label}: 'repeat-acq' tag added")


def process_nifti(file_obj, modality: str, subject):
    """
    Process a NIfTI file object, adding a 'read' tag if necessary.

    Args:
        file_obj: Flywheel file object.
        modality: The modality being processed (e.g., T2w, T1w).
    """
    # Check if the file is a NIfTI file
    try:
        if file_obj.type == 'nifti':
            if subject.startswith("137"):
                file_obj.add_tag('phantom')
                print(f"subject {subject}, {file_obj.name}: 'phantom' tag added for {modality}")
                
            if not file_obj.tags and not subject.startswith("137"):
                file_obj.add_tag('read')
                print(f"subject {subject}, {file_obj.name}: 'read' tag added for {modality}")
            
            else:
                # Add 'read' tag only if none of the QC tags are present
                if not any(tag in file_obj.tags for tag in ['read', 'QC_unclear', 'QC_failed', 'QC_passed','QC-unclear', 'QC-failed', 'QC-passed']):
                    file_obj.add_tag('read')
                    parent_acquisition = file_obj.parent
                    parent_acquisition.add_tag('read')
                    print(f"subject {subject}, {file_obj.name}: 'read' tag added for {modality}")
                else:
                    print(f"subject {subject}, {file_obj.name}: QC tag already present")
        else:
            print(file_obj.name, "is not a NIfTI file. Skipping.")
    except Exception as e:
        print("Caught Exception : ", e)


def tagger(input, T2wQC: bool, T1wQC: bool, FLAIRQC: bool, ADCQC: bool, SessionQC: bool = False):
    """
    Tag files in Flywheel for visual QC tasks.
    """

    # Load configuration and initialize Flywheel client
    config = load_config('/flywheel/v0/config.json')
    fw = initialize_flywheel_client(config)

    # Get the input container, if a file input was provided (not required
    # for a session-level, Session-QC-only run)
    input_container = None
    if 'input' in config.get('inputs', {}):
        hierarchy_id = config['inputs']['input']['hierarchy']['id']
        input_container = fw.get(hierarchy_id)

        # Get the subject label
        subject = fw.get(input_container.parents['subject']).label
        print("Subject is:", subject)

        modality_flags = {'T2w': T2wQC, 'T1w': T1wQC, 'FLAIR': FLAIRQC, 'ADC': ADCQC}

        for file_obj in input_container.files:
            if file_obj.type == 'nifti':
                print("file is:", file_obj.name)

                # Process each QC type
                modality = match_modality(file_obj.name)
                if modality and modality_flags[modality]:
                    process_nifti(file_obj, modality, subject)

    if SessionQC:
        session = fw.get(resolve_session_id(config, input_container))
        tag_session_for_review(fw, session)