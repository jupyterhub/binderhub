"""top-level pytest config

options can only be defined here,
not in binderhub/tests/conftest.py
"""

import nest_asyncio


def pytest_addoption(parser):
    parser.addoption(
        "--helm",
        action="store_true",
        default=False,
        help="Run tests marked with pytest.mark.helm",
    )


def pytest_configure():
    nest_asyncio.apply()
