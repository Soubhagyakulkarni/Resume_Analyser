"""User-safe presentation of expected application errors."""

import streamlit as st

from app.utils.errors import ApplicationError, ProviderRateLimitError, ProviderUnavailableError

# Errors where the file was already parsed — user can retry without re-uploading
_RETRYABLE = (ProviderUnavailableError, ProviderRateLimitError)


def show_application_error(error: ApplicationError, correlation_id: str) -> None:
    st.error(f"{error.user_message} Reference: {correlation_id}")
    if isinstance(error, _RETRYABLE):
        if st.button("🔄 Try Again", key="retry_analysis_btn", type="primary"):
            st.rerun()
