import re

import pytest
from typer.testing import CliRunner
from yarl import URL

from invenio_nrp.cli import app
from invenio_nrp.config import Config

runner = CliRunner()



async def test_add_local_repository(fs, token_a, clear_config):
    config = Config.from_file()
    assert config.repositories == []

    result = runner.invoke(
        app,
        [
            "add",
            "repository",
            "--no-verify-tls",
            "--no-launch-browser",
            "https://127.0.0.1:5000",
            "local",
        ],
        input=f"\n{token_a}\n",
    )
    stdout = result.stdout
    print(stdout)
    assert "Adding repository https://127.0.0.1:5000 with alias local" in stdout
    assert "I will try to open the following url in your browser:" in stdout
    assert "https://127.0.0.1:5000/account/settings/applications/tokens/new" in stdout
    assert "Added repository local -> https://127.0.0.1:5000" in stdout
    assert result.exit_code == 0
    config = Config.from_file()
    assert len(config.repositories) == 1
    assert config.repositories[0].alias == "local"
    assert config.repositories[0].url == URL("https://127.0.0.1:5000")
    assert config.repositories[0].token == token_a
    assert not config.repositories[0].verify_tls



async def test_repository_listing(fs, saved_config_file, in_output):
    result = runner.invoke(app, ["list", "repositories"], catch_exceptions=False)
    stdout = result.stdout
    print(stdout)
    stdout = re.sub(" +", " ", stdout)
    assert in_output(
        stdout,
        """
    local https://127.0.0.1:5000
    zenodo https://www.zenodo.org
                     """,
    )


async def test_repository_listing_details(fs, saved_config_file, in_output):
    result = runner.invoke(
        app, ["list", "repositories", "--verbose"], catch_exceptions=False
    )
    stdout = result.stdout
    print(stdout)
    assert in_output(
        stdout,
        """
Repository 'local'                              
                                                
  URL                   https://127.0.0.1:5000  
  Token                 ***                     
  TLS Verify            skip                    
  Retry Count           5                       
  Retry After Seconds   10                      
  Default                                       
                                                
Repository 'zenodo'                             
                                                
  URL                   https://www.zenodo.org  
  Token                 anonymous               
  TLS Verify            ✓                       
  Retry Count           5                       
  Retry After Seconds   10                      
  Default                                                  
                     """,
    )


async def test_repository_listing_details_json(fs, saved_config_file, in_output):
    result = runner.invoke(
        app,
        ["list", "repositories", "--verbose", "--output-format", "json"],
        catch_exceptions=False,
    )
    stdout = result.stdout
    print(stdout)
    assert in_output(
        stdout,
        """
[
    {
        "alias": "local",
        "url": "https://127.0.0.1:5000",
        "token": "***",
        "tls_verify": false,
        "retry_count": 5,
        "retry_after_seconds": 10,
        "info": null
    },
    {
        "alias": "zenodo",
        "url": "https://www.zenodo.org",
        "token": "anonymous",
        "tls_verify": true,
        "retry_count": 5,
        "retry_after_seconds": 10,
        "info": null
    }
]
""",
    )


async def test_repository_listing_details_yaml(fs, saved_config_file, in_output):
    result = runner.invoke(
        app,
        ["list", "repositories", "--verbose", "--output-format", "yaml"],
        catch_exceptions=False,
    )
    stdout = result.stdout
    print(stdout)
    assert in_output(
        stdout,
        """
- alias: local
  info: null
  retry_after_seconds: 10
  retry_count: 5
  tls_verify: false
  token: '***'
  url: https://127.0.0.1:5000
- alias: zenodo
  info: null
  retry_after_seconds: 10
  retry_count: 5
  tls_verify: true
  token: anonymous
  url: https://www.zenodo.org
""",
    )


async def test_repository_select(fs, saved_config_file):
    result = runner.invoke(
        app, ["select", "repository", "local"], catch_exceptions=False
    )
    stdout = result.stdout
    print(stdout)
    assert 'Selected repository "local"' in stdout
    config = Config.from_file()
    assert config.default_alias == "local"

    result = runner.invoke(
        app, ["select", "repository", "zenodo"], catch_exceptions=False
    )
    stdout = result.stdout
    print(stdout)
    assert 'Selected repository "zenodo"' in stdout
    config = Config.from_file()
    assert config.default_alias == "zenodo"


async def test_repository_enable_disable(fs, saved_config_file):
    result = runner.invoke(
        app, ["enable", "repository", "local"], catch_exceptions=False
    )
    stdout = result.stdout
    print(stdout)
    assert 'Enabled repository "local"' in stdout
    config = Config.from_file()
    assert config.get_repository("local").enabled

    local_repo = next(repo for repo in config.repositories if repo.alias == "local")
    for_url = config.get_repository_from_url(local_repo.url)
    assert for_url is local_repo

    result = runner.invoke(
        app, ["disable", "repository", "local"], catch_exceptions=False
    )
    stdout = result.stdout
    print(stdout)
    assert 'Disabled repository "local"' in stdout
    config = Config.from_file()

    with pytest.raises(ValueError, match="Repository with alias 'local' is disabled"):
        config.get_repository("local")

    assert config.get_repository("zenodo").enabled

    local_repo = next(repo for repo in config.repositories if repo.alias == "local")
    for_url = config.get_repository_from_url(local_repo.url)
    assert for_url is not local_repo


async def test_repository_remove(fs, saved_config_file):
    result = runner.invoke(
        app, ["remove", "repository", "local"], catch_exceptions=False
    )
    stdout = result.stdout
    print(stdout)
    assert 'Removed repository "local"' in stdout
    config = Config.from_file()
    assert len(config.repositories) == 1
    assert config.get_repository("zenodo")

    with pytest.raises(KeyError, match="Repository with alias 'local' not found"):
        config.get_repository("local")


async def test_repository_describe_local(fs, saved_config_file, in_output):
    result = runner.invoke(
        app, ["describe", "repository", "--refresh", "local"], catch_exceptions=False,
        env={"COLUMNS": "200"}
    )
    stdout = result.stdout
    print(stdout)
    assert in_output(
        stdout,
        """
Repository 'local'

  Name                  Test repository for nrp-cmd              
  URL                   https://127.0.0.1:5000                   
  Token                 ***                                      
  TLS Verify            skip                                     
  Retry Count           5                                        
  Retry After Seconds   10                                       
  Default                                                        
  Version               local development                        
  Invenio Version       12.2.4                                   
  Transfers             local-file, url-fetch                    
  Records url           https://127.0.0.1:5000/api/search/       
  User records url      https://127.0.0.1:5000/api/user/search/ 
                                                           
Model 'simple'                                                                       
                                                                                     
  Name                    simple                                                     
  Description                                                                        
  Version                 1.0.0                                                      
  Features                requests, drafts, files                                    
  API                     https://127.0.0.1:5000/api/simple/                         
  HTML                    https://127.0.0.1:5000/simple/                             
  Schemas                 {'application/json': 'https://127.0.0.1:5000/.well-known/repository/schema/simple-1.0.0.json'}                
  Model Schema            https://127.0.0.1:5000/.well-known/repository/models/simple     
  Published Records URL   https://127.0.0.1:5000/api/simple/                         
  User Records URL        https://127.0.0.1:5000/api/user/simple/ 
                     """,
    )
