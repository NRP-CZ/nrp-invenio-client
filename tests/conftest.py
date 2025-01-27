#
# Copyright (C) 2024 CESNET z.s.p.o.
#
# invenio-nrp is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
#
import re
from pathlib import Path

import pytest
from yarl import URL

from invenio_nrp.config import Config, RepositoryConfig

pytest_plugins = ("pytest_asyncio",)

import logging

logging.basicConfig(level=logging.ERROR)

@pytest.fixture(scope="session")
def token_a() -> str:
    """Return the bearer token for the local test repository."""
    return (Path(__file__).parent / "test-repository" / "repo" / ".token_a").read_text().strip()

@pytest.fixture(scope="function")
def nrp_repository_config(token_a):
    """Return the configuration of the NRP client with a local test repository as well as zenodo."""
    tmp_config_file = Path("/tmp/.test-nrp-config.json")
    if tmp_config_file.exists():
        tmp_config_file.unlink()

    config = Config.from_file(tmp_config_file)
    config.add_repository(
        RepositoryConfig(
            alias="local",
            url=URL("https://127.0.0.1:5000"),
            token=token_a,
            verify_tls=False,
            retry_count=5,
            retry_after_seconds=10,
        )
    )
    config.add_repository(
        RepositoryConfig(
            alias="zenodo",
            url=URL("https://www.zenodo.org"),
            token=None,
            verify_tls=True,
            retry_count=5,
            retry_after_seconds=10,
        )
    )
    config.save()
    return config


@pytest.fixture
def in_output():
    def in_output_func(output, expected, ignore_extra_lines=True):
        expected = re.sub(' +', ' ', expected)
        expected_lines = [x.strip() for x in expected.split("\n")]
        expected_lines = [x for x in expected_lines if x]

        output = re.sub(' +', ' ', output)    
        output_lines = [x.strip() for x in output.split("\n")]
        output_lines = [x for x in output_lines if x]
        
        ok = True
        while output_lines and expected_lines:
            if output_lines[0] == expected_lines[0]:
                output_lines.pop(0)
                expected_lines.pop(0)
                ok = True
            else:
                if ok:
                    print("Expected line: ", expected_lines[0])
                ok = False
                print("Skipping line: ", output_lines[0])
                output_lines.pop(0)
        if expected_lines:
            print("Expected lines not found:")
            print("\n".join(expected_lines))
            print("Actual lines:")
            print("\n".join(output_lines))
            return False    

        if output_lines and not ignore_extra_lines:
            print("Extra lines found:")
            print("\n".join(output_lines))
            return False
        
        return True

    return in_output_func