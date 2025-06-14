from src.services.common.context import Context


class PromptsService:
    # TODO: will connect to cloud storage
    def __init__(self, context: Context):
        self.context = context

    async def get_prompt(self, prompt_path: str) -> str:
        if prompt_path == "title_generation":
            return """
Generate a concise and engaging title that summarizes the main topic or theme of the conversation between a user and an AI (or just the user question).
The title should be clear, relevant, and attention-grabbing, ideally no longer than 3-4 words. Consider the key points, questions, or issues discussed in the conversation.
Make sure to not add any special characters or markdown to the title.
Do not add any quotes to the title.
"""
        elif prompt_path == "default":
            return """
You are a helpful assistant that can answer questions and help with tasks.
"""
        else:
            raise ValueError(f"Prompt path {prompt_path} not found")
