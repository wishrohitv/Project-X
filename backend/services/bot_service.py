from database import SessionLocal
from google import genai
from models import Posts, Users
from modules import datetime, json, timezone
from settings import Settings

client = genai.Client()


def generate_bot_response(query: str) -> str | None:
    response = client.models.generate_content(
        model=Settings.GEMINI_MODEL_NAME or "gemini-3.5-flash",
        contents=str(query),
    )
    return response.text


# Tools for accessing post database

query_post_database = {
    "type": "function",
    "name": "query_post_database_function",
    "description": (
        "Retrieve the text of the parent post using its post ID. "
        "Only call this tool when parent_post_id is not null and "
        "the user's question requires context from the parent post."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "parent_post_id": {
                "type": "string",
                "description": "The ID of the parent post.",
            },
        },
        "required": ["parent_post_id"],
    },
}


def query_post_database_function(parent_post_id: str) -> dict:
    session = SessionLocal()

    try:
        parent_post = (
            session.query(Posts, Users.username)
            .join(Users, Posts.user_id == Users.id)
            .filter(
                Posts.id == int(parent_post_id),  # Parent post ID
                Posts.visibility.is_(True),
            )
            .first()
        )

        if not parent_post:
            return {
                "success": False,
                "error": "Parent post not found.",
            }

        post, username = parent_post

        return {
            "success": True,
            "post_id": post.id,
            "username": username,
            "text": post.text,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }

    finally:
        session.close()


def gemini_agent(
    user_id: int,
    post_text: str,
    parent_post_id: int | None,
) -> str | None:
    instruction = (
        "You are NARA, an AI assistant created by Antelope Ltd. "
        "You reply to users' posts similarly to X's Grok. "
        "Your replies are posted publicly under your own profile.\n\n"
        "Rules:\n"
        "- Answer naturally and add sarcasm and humor.\n"
        "- Keep your answer short within a range between 50 to 400 characters.\n"
        "- Don't add **bold** or *italic* formatting to your answers.\n"
        "- Don't add any other formatting to your answers.\n"
        "- If parent_post_id is null, NEVER call the database tool.\n"
        "- Only call the database tool if the user's question requires context from the parent post.\n"
        "- If the post can be answered without the parent post, answer directly.\n\n"
        f"Today's UTC date is {datetime.now(timezone.utc).isoformat()}.\n\n"
        "Expected Input Format:\n"
        "You will receive a JSON object containing the author details and post_text. Parse it and reply to the post_text according to your rules."
    )

    input_message = [
        {
            "role": "user",
            "content": {
                "author": {
                    "user_id": user_id,
                    "post_text": post_text,
                    "parent_post_id": parent_post_id,
                },
            },
        },
    ]

    tools = [query_post_database] if parent_post_id else []

    interaction = client.interactions.create(
        model=Settings.GEMINI_MODEL_NAME or "gemini-3.5-flash",
        system_instruction=str(instruction),
        input=json.dumps(input_message, indent=2),
        tools=tools,
    )

    while interaction.status == "requires_action":
        function_results = []

        for step in interaction.steps:
            if step.name == "query_post_database_function":
                result = query_post_database_function(step.arguments["parent_post_id"])

            function_results.append(
                {
                    "type": "function_result",
                    "name": step.name,
                    "call_id": step.id,
                    "result": result,
                }
            )

        interaction = client.interactions.create(
            model=Settings.GEMINI_MODEL_NAME or "gemini-2.5-flash",
            previous_interaction_id=interaction.id,
            environment=interaction.environment_id,
            input=function_results,
            tools=tools,
        )

    return interaction.output_text
