import openai
from sentence_miner.utils.config import LANGUAGE_MAP

class OpenAIClient:
    def __init__(self, api_key, model_name='gpt-4'):
        self.api_key = api_key
        self.model_name = model_name
        openai.api_key = self.api_key

    def query_openai(self, prompt_text, ocr_language, openai_prompt, user_openai_prompt):
        language_name = LANGUAGE_MAP.get(ocr_language, 'unknown')

        # Use the current prompt settings, including user edits
        prompt_with_language = openai_prompt.replace('{language}', language_name)  # Adjust the system prompt

        # Attach the extracted text at the end of the user-defined prompt
        user_prompt_with_text = user_openai_prompt + "\n\n" + prompt_text

        messages = [
            {"role": "system", "content": prompt_with_language},
            {"role": "user", "content": user_prompt_with_text}
        ]

        response = openai.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=1000
        )

        return response.choices[0].message.content