"""Import smoke tests: every library module must import without side effects."""
import importlib

import pytest

CORE_MODULES = ["Log", "Settings", "Emergency", "DirectoryManager",
                "SysMonitor", "Modes", "Engine"]
WEB_MODULES = ["Web_Logs", "ReportGenerator", "WebSysMonitor",
               "BlueWeb", "BluewebParseai", "Web_Backend"]
ADMIN_MODULES = ["Commands", "AdminPanel", "Admin", "Dashboard"]


@pytest.mark.parametrize("modname", CORE_MODULES + WEB_MODULES + ADMIN_MODULES)
def test_module_imports(modname):
    mod = importlib.import_module(modname)
    assert mod is not None


def test_optional_deps_are_lazy():
    """Missing optional deps must not break importing their host modules."""
    import BlueWeb
    import BluewebParseai
    import SysMonitor
    # These attributes exist regardless of whether the optional dep is installed.
    assert hasattr(BlueWeb, "run_bluetooth_scan")
    assert hasattr(BluewebParseai, "BlueAi")
    assert hasattr(SysMonitor, "Sensor")
