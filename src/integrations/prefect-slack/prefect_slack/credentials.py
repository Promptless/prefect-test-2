"""Credential classes use to store Slack credentials."""

from typing import Any, Optional, Union

from pydantic import Field, SecretStr
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.webhook.async_client import AsyncWebhookClient
from slack_sdk.webhook.client import WebhookClient

from prefect._internal.compatibility.async_dispatch import async_dispatch
from prefect.blocks.core import Block
from prefect.blocks.notifications import NotificationBlock


class SlackCredentials(Block):
    """
    Block holding Slack credentials for use in tasks and flows.

    Args:
        token: Bot user OAuth token for the Slack app used to perform actions.

    Examples:
        Load stored Slack credentials:
        ```python
        from prefect_slack import SlackCredentials
        slack_credentials_block = SlackCredentials.load("BLOCK_NAME")
        ```

        Get a Slack client:
        ```python
        from prefect_slack import SlackCredentials
        slack_credentials_block = SlackCredentials.load("BLOCK_NAME")
        client = slack_credentials_block.get_client()
        ```
    """  # noqa E501

    _block_type_name = "Slack Credentials"
    _logo_url = "https://cdn.sanity.io/images/3ugk85nk/production/c1965ecbf8704ee1ea20d77786de9a41ce1087d1-500x500.png"  # noqa
    _documentation_url = "https://prefecthq.github.io/prefect-slack/credentials/#prefect_slack.credentials.SlackCredentials"  # noqa

    token: SecretStr = Field(
        default=...,
        description="Bot user OAuth token for the Slack app used to perform actions.",
    )

    def get_client(self) -> AsyncWebClient:
        """
        Returns an authenticated `AsyncWebClient` to interact with the Slack API.
        """
        return AsyncWebClient(token=self.token.get_secret_value())


async def _notify_async(obj: Any, body: str, subject: Optional[str] = None):
    client = obj.get_client()

    response = await client.send(text=body)

    obj._raise_on_failure(response)


class SlackWebhook(NotificationBlock):
    """
    Block holding a Slack webhook for use in tasks and flows.

    Args:
        url: Slack webhook URL which can be used to send messages
            (e.g. `https://hooks.slack.com/XXX`).

    Examples:
        Load stored Slack webhook:
        ```python
        from prefect_slack import SlackWebhook
        slack_webhook_block = SlackWebhook.load("BLOCK_NAME")
        ```

        Get a Slack webhook client:
        ```python
        from prefect_slack import SlackWebhook
        slack_webhook_block = SlackWebhook.load("BLOCK_NAME")
        client = slack_webhook_block.get_client()
        ```

        Send a notification in Slack:
        ```python
        from prefect_slack import SlackWebhook
        slack_webhook_block = SlackWebhook.load("BLOCK_NAME")
        slack_webhook_block.notify("Hello, world!")
        ```
    """

    _block_type_name = "Slack Incoming Webhook"
    _logo_url = "https://images.ctfassets.net/gm98wzqotmnx/7dkzINU9r6j44giEFuHuUC/85d4cd321ad60c1b1e898bc3fbd28580/5cb480cd5f1b6d3fbadece79.png?h=250"  # noqa
    _documentation_url = "https://prefecthq.github.io/prefect-slack/credentials/#prefect_slack.credentials.SlackWebhook"  # noqa

    url: SecretStr = Field(
        default=...,
        title="Webhook URL",
        description="Slack webhook URL which can be used to send messages.",
        examples=["https://hooks.slack.com/XXX"],
    )

    def get_client(
        self, sync_client: bool = False
    ) -> Union[AsyncWebhookClient, WebhookClient]:
        """
        Returns an authenticated `AsyncWebhookClient` to interact with the configured
        Slack webhook.
        """
        if sync_client:
            return WebhookClient(url=self.url.get_secret_value())
        return AsyncWebhookClient(url=self.url.get_secret_value())

    def _raise_on_failure(self, response: Any):
        # prefect>=2.17.2 added a means for notification blocks to raise errors on
        # failures. This is not available in older versions, so we need to check if the
        # private base class attribute exists before using it.
        if getattr(self, "_raise_on_failure", False):  # pragma: no cover
            try:
                from prefect.blocks.abstract import NotificationError
            except ImportError:
                NotificationError = Exception

            if response.status_code >= 400:
                raise NotificationError(f"Failed to send message: {response.body}")

    async def notify_async(self, body: str, subject: Optional[str] = None):
        """
        Sends a message to the Slack channel.
        """
        await _notify_async(self, body, subject)

    @async_dispatch(_notify_async)  # type: ignore
    def notify(self, body: str, subject: Optional[str] = None):
        """
        Sends a message to the Slack channel.
        """
        client = self.get_client(sync_client=True)

        response = client.send(text=body)

        self._raise_on_failure(response)
