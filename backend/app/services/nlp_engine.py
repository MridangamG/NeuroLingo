import json
from typing import Dict, Any
from google import genai
from app.core.config import settings
from app.services.retry import retry_with_backoff


class NLPEngine:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def _strip_markdown(self, text: str) -> str:
        """Strip markdown code fences from LLM responses."""
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:-3].strip()
        elif text.startswith('```'):
            text = text[3:-3].strip()
        return text

    async def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyze the incoming text for intent, tone, emotion, and figurative language using Gemini.
        """
        prompt = f"""
        Analyze the following text from a user communicating socially.
        Extract the following:
        1. intent: What is the true intent of the message?
        2. tone: What is the tone? (e.g., formal, informal, passive-aggressive, sincere)
        3. figurative_language: Boolean indicating if idioms/metaphors are used.
        4. ambiguity: The level of ambiguity (Low, Medium, High).

        Text to analyze: "{text}"

        Respond ONLY with a valid JSON object without markdown formatting. Format:
        {{
            "intent": "string",
            "tone": "string",
            "figurative_language": bool,
            "ambiguity": "string"
        }}
        """
        try:
            response = await retry_with_backoff(
                self.client.models.generate_content,
                model='gemini-2.5-flash',
                contents=prompt,
            )
            result = json.loads(self._strip_markdown(response.text))
            return result
        except Exception as e:
            print(f"Error analyzing text: {e}")
            return {
                "intent": "Error in analysis",
                "tone": "Unknown",
                "figurative_language": False,
                "ambiguity": "Unknown",
            }


nlp_engine = NLPEngine()
