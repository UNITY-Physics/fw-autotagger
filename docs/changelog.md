# Changelog
25 August 2026:
"version": "0.1.6"
Fixed repeat-acquisition detection to also normalize the trailing series-number suffix dcm2niix appends before the file extension (previously only the leading prefix was stripped). Made the "input" file optional so the gear can run directly against a session (no file input) when only "Session-QC" is enabled; session resolution now falls back to the job's destination container in that case.

24 August 2026:
"version": "0.1.5"
Added "Session-QC" config option. When enabled, tags the session with 'session-read' for the session-level reader task, and additionally with 'repeat-acq' if the session contains repeat acquisitions of the same scan type (same QC modality and normalized file name, run under different series numbers).

31 July 2026:
"version": "0.1.2"
Add phantom-tagging of nifti files to avoid neuroimaging analyses running on phantoms

28th July 2025
"version": "0.1.1"
Added session tagging due to flywheel issues with file versioning. This will enable filtering by acqusition when assigning QC tasks.

22st March 2024
"version": "0.0.2"

- Input file captures the acquisition container ID, so ammended to tag this level. 

---
21st March 2024
"version": "0.0.1"

- Initial build