# agent.py
import json
import asyncio
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import google, noise_cancellation

load_dotenv()

class Assistant(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful voice AI assistant.")

async def entrypoint(ctx: agents.JobContext):
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            model="gemini-2.0-flash-exp",
            voice="Puck",
            temperature=0.8,
            instructions="You are a helpful assistant",
        ),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()),
    )

    async def publish_action(action_obj):
        """Send navigation action to frontend via LiveKit data channel"""
        try:
            await ctx.room.local_participant.publish_data(
                json.dumps(action_obj), reliable=True
            )
        except Exception as e:
            print("publish_data failed:", e)

    @session.on("conversation_item_added")
    def on_item(item):
        """Detect user command and publish action"""
        try:
            text = getattr(item, "content", "") or ""
            low = text.lower()
            if "skills" in low:
                asyncio.create_task(publish_action({"action": "SHOW_SKILLS"}))
                asyncio.create_task(session.generate_reply(instructions="Showing your skills."))
            elif "projects" in low:
                asyncio.create_task(publish_action({"action": "SHOW_PROJECTS"}))
                asyncio.create_task(session.generate_reply(instructions="Here are your projects."))
            elif "about" in low:
                asyncio.create_task(publish_action({"action": "SHOW_ABOUT"}))
                asyncio.create_task(session.generate_reply(instructions="About me section."))
            elif "resume" in low or "cv" in low:
                asyncio.create_task(publish_action({"action": "SHOW_RESUME"}))
                asyncio.create_task(session.generate_reply(instructions="Displaying your resume."))
        except Exception as e:
            print("on_item error", e)

    # Initial greeting
    await session.generate_reply(instructions="Hello! I am your AI assistant. You can ask me to show skills, projects, about me, or resume.")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
