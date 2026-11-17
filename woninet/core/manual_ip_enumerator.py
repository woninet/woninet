from woninet.core.models import Device
from woninet.core.diagnostic import DiagnosticManager


class ManualIPEnumerator:
    """
    Build a dictionary of candidate devices for user-provided IP addresses.
    """

    def __init__(self, diagnostics: DiagnosticManager) -> None:
        """
        Initialize the manual IP enumerator with the diagnostics instance collect issues.

        Args:
            diagnostics (DiagnosticManager): Instance of DiagnosticManager to collect utility's
                issues.
        """
        self.diagnostics = diagnostics

    def enumerate(self, ip_list: list[str]) -> dict[str, str]:
        devices = {}
        for ip in ip_list:
            devices[ip] = Device(ip=ip)
        return devices

    def enumerate_range(self, ip_range: str) -> dict[str, Device]:
        """
        Build a dictionary of candidate devices for user-provided IP addresses range.

        Args:
            ip_range (str): IP address as a range (e.g. 192.168.1.10-50).

        Raises:
            ValueError: If the range notation is not in the last octet.
        """
        base, last_octet = ip_range.rsplit(".", maxsplit=1)
        if "-" in base:
            self.diagnostics.add_issue(
                "configuration",
                "INVALID_IP_RANGE_FORMAT",
                "Range enumeration is only supported on the last octet. check `target_ip_list` key in `config.json`.",
            )
            raise ValueError("Range enumeration is only supported on the last octet.")
        start, stop = last_octet.split("-")
        devices = {}
        for i in range(int(start), int(stop) + 1):
            ip = f"{base}.{i}"
            devices[ip] = Device(ip=ip)
        return devices
