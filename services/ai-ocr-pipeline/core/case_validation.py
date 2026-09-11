"""
core/case_validation.py
-------------------------
Member 6 scope. Pure validation logic for the officer upload flow, kept
separate from app.py so it can be unit-tested without loading the GPU model.

Rule:
  - "Register New FIR (first time)": FIR upload is MANDATORY.
      Supporting documents are optional.
  - "Existing Case Folder (update / add documents)": FIR upload is NOT
      mandatory. At least one of (FIR, supporting documents) must be given.
"""

NEW_FIR_MODE = "Register New FIR (first time)"
EXISTING_CASE_MODE = "Existing Case Folder (update / add documents)"


def validate_case_submission(case_mode: str, fir_file, supporting_files: list) -> str | None:
    """
    Returns an error message string if the submission is invalid, or None
    if it's valid and processing should proceed.
    """
    supporting_files = supporting_files or []

    if case_mode == NEW_FIR_MODE:
        if not fir_file:
            return ("ERROR: FIR upload is mandatory when registering a new FIR. "
                     "Supporting documents are optional at this stage.")
        return None

    if case_mode == EXISTING_CASE_MODE:
        if not fir_file and not supporting_files:
            return ("ERROR: Please upload at least one document (FIR update or "
                     "a supporting document).")
        return None

    return f"ERROR: Unrecognized case mode '{case_mode}'."
