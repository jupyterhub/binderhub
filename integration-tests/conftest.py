import nest_asyncio


def pytest_configure(config):
    # Required for playwright to be run from within pytest
    nest_asyncio.apply()
