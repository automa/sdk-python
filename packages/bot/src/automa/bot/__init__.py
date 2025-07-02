from ._client import AsyncAutoma, Automa
from ._types import (
    GenericTaskItem,
    Org,
    ProposalTaskItem,
    Repo,
    Task,
    TaskForCode,
    TaskItem,
    WebhookEventType,
    WebhookPayload,
    WebhookProposalAcceptedData,
    WebhookProposalAcceptedPayload,
    WebhookProposalRejectedData,
    WebhookProposalRejectedPayload,
    WebhookTaskCreatedData,
    WebhookTaskCreatedPayload,
)
from .resources import (
    AsyncCodeResource,
    CodeCleanupParams,
    CodeDownloadParams,
    CodeFolder,
    CodeProposeParams,
    CodeResource,
)

__all__ = [
    "Automa",
    "AsyncAutoma",
    "AsyncCodeResource",
    "CodeResource",
    "CodeFolder",
    "CodeCleanupParams",
    "CodeDownloadParams",
    "CodeProposeParams",
    "ProposalTaskItem",
    "GenericTaskItem",
    "TaskItem",
    "Task",
    "TaskForCode",
    "Repo",
    "Org",
    "WebhookEventType",
    "WebhookTaskCreatedData",
    "WebhookTaskCreatedPayload",
    "WebhookProposalAcceptedData",
    "WebhookProposalAcceptedPayload",
    "WebhookProposalRejectedData",
    "WebhookProposalRejectedPayload",
    "WebhookPayload",
]

# Update the __module__ attribute for exported symbols so that
# error messages point to this module instead of the module
# it was originally defined in, e.g.
# automa._exceptions.NotFoundError -> automa.NotFoundError
__locals = locals()

for __name in __all__:
    if not __name.startswith("__"):
        try:
            __locals[__name].__module__ = "automa"
        except (TypeError, AttributeError):
            # Some of our exported symbols are builtins which we can't set attributes for.
            pass
