import json
import time

from typer.testing import CliRunner

from invenio_nrp.cli import app

runner = CliRunner()


def test_create_record(fs, saved_config_file, default_local, in_output):
    # region: Create a record
    result = runner.invoke(
        app,
        [
            "create",
            "record",
            "--model",
            "simple",
            "--community",
            "acom",
            json.dumps(
                {
                    "title": "Test record A",
                }
            ),
        ],
        catch_exceptions=False,
    )
    create_stdout = result.stdout
    print(create_stdout)
    assert in_output(
        create_stdout,
        """
  state                     draft                                                                
  Metadata                                                                                       
      title                 Test record A   
      """,
    )
    rec = [x.strip() for x in create_stdout.splitlines() if x.strip()][0]
    rec_id = rec.split()[-1]
    assert rec_id[5] == "-"
    print("Record ID: ", rec_id)
    # endregion

    # region: Get the record
    result = runner.invoke(
        app,
        [
            "get",
            "record",
            "--draft",
            rec_id,
            "--expand",
        ],
        catch_exceptions=False,
    )
    stdout = result.stdout
    print(stdout)
    assert in_output(stdout, create_stdout)
    # endregion

    # region: Update the record
    result = runner.invoke(
        app,
        [
            "update",
            "record",
            rec_id,
            json.dumps(
                {
                    "title": "Test record B",
                }
            ),
        ],
        catch_exceptions=False,
    )
    update_stdout = result.stdout
    print(update_stdout)
    assert in_output(
        update_stdout,
        """
    state                     draft
    Metadata
        title                 Test record B
        """,
    )
    # endregion

    # region: Get the record to check if the metadata has been updated
    result = runner.invoke(
        app,
        [
            "get",
            "record",
            "--draft",
            rec_id,
            "--expand",
        ],
        catch_exceptions=False,
    )
    stdout = result.stdout
    print(stdout)
    assert in_output(
        stdout,
        """
    state                     draft
    Metadata
        title                 Test record B""",
    )
    # endregion

    # region: Search for the record by its id
    # propagating the changes to the search index takes 
    # app. 5 seconds, so waiting a bit longer here
    time.sleep(10)
    result = runner.invoke(
        app,
        [
            "search",
            "records",
            "--drafts",
            f"id:{rec_id}",
        ],
        catch_exceptions=False,
    )
    search_stdout = result.stdout
    print("Search result: ")
    print(search_stdout)
    assert in_output(search_stdout, f"Record {rec_id}")
    assert in_output(
        search_stdout,
        """
    state                     draft
    Metadata
        title                 Test record B
        """,
    )
    # endregion
