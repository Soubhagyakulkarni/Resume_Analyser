"""UI tests for the session-only resume builder."""

from streamlit.testing.v1 import AppTest


def _app_source() -> str:
    return """
import streamlit as st
from app.pages.resume_builder import render_resume_builder

class FakeResumeService:
    max_resume_chars = 50000

    def parse(self, filename, content):
        raise AssertionError("No file should be parsed in this test")

render_resume_builder(FakeResumeService())
"""


def test_builder_shows_preview_after_user_enters_resume_content():
    app = AppTest.from_string(_app_source()).run(timeout=20)
    assert not app.exception

    app.text_input(key="resume_builder_name").set_value("Asha Student").run(timeout=20)
    app.text_area(key="resume_builder_projects").set_value("Created a study planner").run(
        timeout=20
    )

    assert not app.exception
    assert any("Asha Student" in heading.value for heading in app.subheader)
    assert "resume_builder_projects" in app.session_state
    assert app.session_state["resume_builder_projects"] == "Created a study planner"


def test_existing_resume_text_can_be_edited_and_previewed():
    app = AppTest.from_string(_app_source()).run(timeout=20)
    assert not app.exception

    app.text_area(key="resume_builder_editor_0").set_value(
        "Education\nBSc Computer Science\nProjects\nBuilt an app"
    ).run(timeout=20)

    assert not app.exception
    assert "BSc Computer Science" in app.session_state["resume_builder_existing_text"]
