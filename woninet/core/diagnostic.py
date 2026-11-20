from typing import TypedDict, Optional
from uuid import uuid4


class DiagnosticIssue(TypedDict):
    """
    Represents a single diagnostic issue.

    Attributes:
        id: Unique identifier for the issue.
        code: Short code describing the issue type.
        message: Human-readable description of the issue.
        docs_url: The documentation guide, if any.
    """

    id: str
    code: str
    message: str
    docs_url: Optional[str]


class DiagnosticManager:
    """
    Collects and exposes diagnostic issues raised during execution.

    Attributes:
        issues: A dictionary of registered diagnostic issues.
    """

    def __init__(self) -> None:
        """
        Initialize an empty diagnostic issue registry.
        """
        self.issues: dict[str, DiagnosticIssue] = {}

    def add_issue(
        self, component: str, code: str, message: str, docs_url: Optional[str] = None
    ) -> None:
        """
        Register a new diagnostic issue.

        Args:
            component: Name of the component associated with the issue.
            code: Short code describing the issue type.
            message: Human-readable explanation of the issue.
            docs_url: The documentation guide, if required.
        """
        self.issues[component] = {
            "id": self._generate_id(),
            "code": code,
            "message": message,
            "docs_url": docs_url,
        }

    def remove_issue(self, component: str) -> None:
        """
        Remove the issue matching `component`.

        Args:
            component (str): Name of the component whose issue should be removed.
        """
        self.issues.pop(component, None)

    def remove_all(self) -> None:
        """
        Remove all registered diagnostic issues.
        """
        self.issues = {}

    def list_issues(self) -> dict[str, DiagnosticIssue]:
        """
        Return all recorded diagnostic issues.

        Returns:
            dict[str, DiagnosticIssue]: The dictionary of issues currently tracked by the manager.
        """
        return self.issues.copy()

    def _generate_id(self) -> str:
        """
        Generate a short unique identifier for a diagnostic issue.

        Returns:
            str: An 8-character hexadecimal identifier.
        """
        return uuid4().hex[:8]
