from ankithis_api.services.youtube.transcript import transcript_to_text, transcript_word_count


def test_transcript_to_text():
    segments = [
        {"start": 0, "duration": 5, "text": "Hello world"},
        {"start": 5, "duration": 5, "text": "this is a test"},
    ]
    assert transcript_to_text(segments) == "Hello world this is a test"


def test_transcript_word_count():
    segments = [
        {"start": 0, "duration": 5, "text": "Hello world"},
        {"start": 5, "duration": 5, "text": "this is a test"},
    ]
    assert transcript_word_count(segments) == 6


def test_empty_transcript():
    assert transcript_to_text([]) == ""
    assert transcript_word_count([]) == 0
