"""Acquisition platform, classification, inspection, resolution, policy, and browser bridge."""

from shusha.acquisition.browser import (
    BrowserBridge,
    BrowserBridgeConfig,
    BrowserMessage,
    BrowserResponse,
    BrowserValidationError,
    read_native_message,
    write_native_message,
)
from shusha.acquisition.detector import AcquisitionDetector
from shusha.acquisition.fake import FakeAcquisitionProvider, FakeHttpHeaderFetcher
from shusha.acquisition.inbox import AcquisitionInbox
from shusha.acquisition.inspector import (
    AcquisitionInspector,
    DefaultHttpHeaderFetcher,
    HttpHeaderFetcher,
    InspectionResult,
)
from shusha.acquisition.policy import AcquisitionPolicyEngine, AcquisitionRule
from shusha.acquisition.resolver import AcquisitionResolver, ResolutionResult

__all__ = [
    "AcquisitionDetector",
    "AcquisitionInbox",
    "AcquisitionInspector",
    "AcquisitionPolicyEngine",
    "AcquisitionResolver",
    "AcquisitionRule",
    "BrowserBridge",
    "BrowserBridgeConfig",
    "BrowserMessage",
    "BrowserResponse",
    "BrowserValidationError",
    "DefaultHttpHeaderFetcher",
    "FakeAcquisitionProvider",
    "FakeHttpHeaderFetcher",
    "HttpHeaderFetcher",
    "InspectionResult",
    "ResolutionResult",
    "read_native_message",
    "write_native_message",
]
