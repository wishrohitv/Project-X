import json
from typing import Any, Dict

from flask import Response


class SuccessResponse(Response):
    def __init__(
        self,
        data: str | Dict[str, Any],
        status_code: int = 200,
        message: str = "Request successful",
    ):
        body = json.dumps({"data": data, "message": message, "code": status_code})

        super().__init__(
            response=body,
            status=status_code,
            mimetype="application/json",
        )
