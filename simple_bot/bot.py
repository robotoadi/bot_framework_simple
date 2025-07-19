# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from botbuilder.core import ActivityHandler, TurnContext, UserState
from botbuilder.schema import ChannelAccount, Activity
from azure_openai import call_azure_openai_agent

class MyBot(ActivityHandler):
    # See https://aka.ms/about-bot-activity-message to learn more about the message and other activity types.
    # https://deepwiki.com/microsoft/botbuilder-python/2.2-activity-handling

    def __init__(self, user_state: UserState):
        if user_state is None:
            raise TypeError(
                "[MyBot]: Missing parameter. user_state is required but None was given"
            )

        self.user_state = user_state

    async def on_message_activity(self, turn_context: TurnContext):
        response = await call_azure_openai_agent(turn_context.activity.text)
        await turn_context.send_activity(Activity(type="message", text=response))

    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Hello and welcome!")

