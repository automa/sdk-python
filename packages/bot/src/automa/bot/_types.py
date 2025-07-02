from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Literal, Mapping, NotRequired, TypedDict, Union

from httpx._types import QueryParamTypes, RequestExtensions


class Omit:
    """In certain situations you need to be able to represent a case where a default value has
    to be explicitly removed and `None` is not an appropriate substitute, for example:

    ```py
    # as the default `Content-Type` header is `application/json` that will be sent
    client.post("/upload/files", files={"file": b"my raw file content"})

    # you can't explicitly override the header as it has to be dynamically generated
    # to look something like: 'multipart/form-data; boundary=0d8382fcf5f8c3be01ca2e11002d2983'
    client.post(..., headers={"Content-Type": "multipart/form-data"})

    # instead you can remove the default `application/json` header by passing Omit
    client.post(..., headers={"Content-Type": Omit()})
    ```
    """

    def __bool__(self) -> Literal[False]:
        return False


Headers = Mapping[str, Union[str, Omit]]


class RequestOptions(TypedDict, total=False):
    json: Any | None
    headers: Headers | None
    params: QueryParamTypes | None
    extensions: RequestExtensions | None
    stream: bool | None


class ProposalTaskItem(TypedDict):
    id: int
    type: Literal["proposal"]
    data: ProposalTaskItemData
    bot_id: int
    repo_id: int

    class ProposalTaskItemData(TypedDict):
        prId: int
        prNumber: int
        prTitle: str
        prHead: str
        prBase: str
        prState: Literal["open", "closed"]
        prMerged: bool


class GenericTaskItem(TypedDict):
    id: int
    type: Literal["origin", "message", "repo", "bot", "activity"]
    data: Dict[str, Any]
    bot_id: NotRequired[int]
    repo_id: NotRequired[int]


TaskItem = Union[ProposalTaskItem, GenericTaskItem]


class Task(TypedDict):
    id: int
    title: str


class TaskForCode(Task):
    token: str
    items: list[TaskItem]


class Repo(TypedDict):
    id: int
    name: str
    is_private: bool


class Org(TypedDict):
    id: int
    name: str
    provider_type: Literal["github", "gitlab"]


class WebhookEventType(Enum):
    TASK_CREATED = "task.created"
    PROPOSAL_ACCEPTED = "proposal.accepted"
    PROPOSAL_REJECTED = "proposal.rejected"


class WebhookTaskCreatedData(TypedDict):
    task: TaskForCode
    repo: Repo
    org: Org


class WebhookProposalClosedData(TypedDict):
    proposal: ProposalTaskItem
    task: Task
    org: Org


WebhookProposalAcceptedData = WebhookProposalClosedData
WebhookProposalRejectedData = WebhookProposalClosedData


class WebhookTaskCreatedPayload(TypedDict):
    id: str
    timestamp: str
    type: Literal[WebhookEventType.TASK_CREATED]
    data: WebhookTaskCreatedData


class WebhookProposalAcceptedPayload(TypedDict):
    id: str
    timestamp: str
    type: Literal[WebhookEventType.PROPOSAL_ACCEPTED]
    data: WebhookProposalAcceptedData


class WebhookProposalRejectedPayload(TypedDict):
    id: str
    timestamp: str
    type: Literal[WebhookEventType.PROPOSAL_REJECTED]
    data: WebhookProposalRejectedData


WebhookPayload = Union[
    WebhookTaskCreatedPayload,
    WebhookProposalAcceptedPayload,
    WebhookProposalRejectedPayload,
]
