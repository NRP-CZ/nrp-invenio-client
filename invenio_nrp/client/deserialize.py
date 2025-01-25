import json as _json
import logging
from typing import Any, Optional, cast, get_args, get_origin

from ..converter import converter

log = logging.getLogger("invenio_nrp.client.deserialize")


def deserialize_rest_response[T](
    connection: Any,
    communication_log: logging.Logger,
    json_payload: bytes,
    result_class: type[T],
    result_context: dict[str, Any] | None,
    etag: Optional[str],
) -> T:
    try:
        if communication_log.isEnabledFor(logging.INFO):
            communication_log.info("%s", _json.dumps(_json.loads(json_payload)))
        if get_origin(result_class) is list:
            arg_type = get_args(result_class)[0]
            return cast(
                result_class,
                [
                    converter.structure(
                        {
                            **x,
                            # "context": result_context,
                        },
                        arg_type,
                    )
                    for x in _json.loads(json_payload)
                ],
            )
        ret = converter.structure(
            {
                **_json.loads(json_payload),
                # "context": result_context,
            },
            result_class,
        )
        if hasattr(ret, "_set_connection_params"):
            ret._set_connection_params(connection, etag)
        return ret
    except Exception as e:
        log.error("Error validating %s with %s", json_payload, result_class)
        raise e
