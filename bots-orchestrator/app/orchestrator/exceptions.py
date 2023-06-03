class UnsupportedConferencingPlatformError(Exception):
    """Unsupported conferencing platform."""


class ConferenceAlreadyBeingRecordedError(Exception):
    """Trying to record conference that already being recorded."""


class ConferenceIsNotBeingRecordedError(Exception):
    """Trying to stop recording of conference which is not being recorded."""
