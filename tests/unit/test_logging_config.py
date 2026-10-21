"""Tests for structured logging and sensitive exception redaction."""

import json
import logging
import sys

from app.utils.logging_config import PrivacySafeJsonFormatter


def test_formatter_emits_structured_fields_without_exception_text():
    try:
        raise ValueError("resume contents must not be logged")
    except ValueError:
        record = logging.LogRecord(
            name="resume_analyzer.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="Analysis failed correlation_id=%s",
            args=("opaque-id",),
            exc_info=sys.exc_info(),
        )

    rendered = PrivacySafeJsonFormatter().format(record)
    event = json.loads(rendered)
    assert event["message"] == "Analysis failed correlation_id=opaque-id"
    assert event["exception_type"] == "ValueError"
    assert "resume contents" not in rendered
