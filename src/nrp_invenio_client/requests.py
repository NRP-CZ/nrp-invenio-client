from typing import Any


class NRPRecordRequestType:
    """
    Class to represent a request type for a NRP record.
    The class is never instantiated directly as request types
    are defined during development and can not
    be created or modified during runtime.
    """

    def __init__(self, record, request_type, requests):
        self._record = record
        self._request_type = request_type
        self._requests = {}
        for r in requests:
            r = NRPRecordRequest(record, self, r)
            self._requests[r.request_id] = r

    @property
    def type_id(self):
        """
        Type_id of the request
        """
        return self._request_type["type_id"]

    @property
    def can_create(self):
        """
        Returns True if the current user can create a new request of this type
        """
        return "create" in self._request_type["links"]["actions"]

    def create(self, metadata=None, submit=True) -> "NRPRecordRequest":
        """
        Create a new request of this type
        :param metadata:    optional metadata of the request (thus some requests might require some metadata)
        :param submit:      if True, the request will be submitted immediately
        :return:            created request
        """
        if not self.can_create:
            raise PermissionError(
                f"User can not create a request of type {self.type_id}"
            )

        request = self._record._client.post(
            self._request_type["links"]["actions"]["create"], data=metadata or {}
        )
        request = NRPRecordRequest(self._record, self, request)
        self._requests[request.request_id] = request
        if submit:
            request.submit()
        return request

    def __iter__(self):
        """
        Iterate over all requests of this type
        """
        return iter(self._requests.values())

    def get(self, item_id, default=None):
        return self._requests.get(item_id, default)

    def submitted_requests(self):
        """
        Return all submitted requests
        """
        return [x for x in self._requests if x.status == "submitted"]

    def cancelled_requests(self):
        """
        Return all cancelled requests
        """
        return [x for x in self._requests if x.status == "cancelled"]

    def accepted_requests(self):
        """
        Return all accepted requests
        """
        return [x for x in self._requests if x.status == "accepted"]

    def declined_requests(self):
        """
        Return all declined requests
        """
        return [x for x in self._requests if x.status == "declined"]

    def expired_requests(self):
        """
        Return all expired requests
        """
        return [x for x in self._requests if x.status == "expired"]

    def to_dict(self):
        """
        Convert to dict
        """
        return {
            **self._request_type,
            "requests": [x.to_dict() for x in self._requests.values()],
        }


class NRPRecordRequest:
    def __init__(self, record, request_type: NRPRecordRequestType, request: Any):
        self._record = record
        self._request_type = request_type
        self._request = request

    @property
    def request_id(self):
        return self._request["id"]

    @property
    def status(self):
        return self._request["status"]

    @property
    def topic(self):
        return self._request["topic"]

    @property
    def creator(self):
        return self._request["creator"]

    @property
    def receiver(self):
        return self._request["receiver"]

    @property
    def data(self):
        return self._request

    @property
    def payload(self):
        return self._request.setdefault("data", {}).setdefault("payload", {})

    @payload.setter
    def payload(self, value):
        self._request.setdefault("data", {})["payload"] = value

    def refresh(self):
        self._request = self._record._client.get(self._request["links"]["self"])

    def save(self):
        self._request = self._record._client.put(
            self._request["links"]["self"], data=self._request
        )

    def cancel(self, reason=None):
        self._change_state("cancel", reason)

    def accept(self, reason=None):
        self._change_state("accept", reason)

    def decline(self, reason=None):
        self._change_state("decline", reason)

    def submit(self, reason=None):
        self._change_state("submit", reason)

    def _change_state(self, action, reason=None):
        if reason:
            data = {"payload": {"content": reason}}
        else:
            data = None
        if action not in self._request["links"]["actions"]:
            available_actions = ", ".join(self._request["links"]["actions"].keys())
            raise ValueError(
                f"Action '{action}' not available for request {self.request_id}. "
                f"Available actions: {available_actions}"
            )

        ret = self._record._client.post(
            self._request["links"]["actions"][action], data=data
        )
        self._request = ret

    def to_dict(self):
        return self._request


class NRPRecordRequests:
    def __init__(self, record, request_types, requests):
        by_type = {}

        for rt in request_types:
            type_id = rt["type_id"]
            by_type[type_id] = (rt, [])

        for r in requests:
            type_id = r["type"]
            if type_id not in by_type:
                by_type[type_id] = ({"type_id": type_id, "links": {"actions": {}}}, [])
            by_type[type_id][1].append(r)

        self._requests = {
            k: NRPRecordRequestType(record, x[0], x[1]) for k, x in by_type.items()
        }

    def __iter__(self):
        return iter(self._requests.values())

    def __getitem__(self, item):
        return self._requests[item]

    def get(self, request_type, item_id):
        return self._requests[request_type][item_id]

    def create(self, request_type, metadata=None, submit=True):
        if request_type not in self._requests:
            raise KeyError(f"Request type {request_type} not found")
        return self._requests[request_type].create(metadata, submit)

    def to_dict(self):
        return {x.type_id: x.to_dict() for x in self._requests.values()}
