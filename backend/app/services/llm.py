import json
from typing import Dict, Any
from google import genai
from app.core.config import settings
from app.services.retry import retry_with_backoff


class LLMPipeline:
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

    def _extract_meaning(self, verification: dict, raw_result: dict) -> str:
        """Safely extract a plain-string meaning from verifier output."""
        meaning = verification.get("corrected_meaning", raw_result.get("meaning", ""))
        if isinstance(meaning, dict):
            return meaning.get("meaning", "Meaning unknown")
        if isinstance(meaning, str):
            try:
                parsed = json.loads(meaning)
                if isinstance(parsed, dict):
                    return parsed.get("meaning", meaning)
            except (json.JSONDecodeError, ValueError):
                pass
        return meaning

    async def translate_to_structured(self, text: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert socially nuanced language into structured meaning using Generator + Verifier.
        """
        generator_prompt = f"""
        You are a specialized AI that translates neurotypical socially ambiguous text into literal, structured actions for autistic individuals.
        Given the original message and its NLP analysis, provide a structured meaning translation suitable for neurodiverse individuals.
        Original: "{text}"
        Analysis: {json.dumps(analysis)}

        Extract:
        1. action: The core action requested or implied.
        2. urgency: The urgency level (Low, Medium, High).
        3. meaning: A clear, literal explanation of what the speaker means without idioms or passive phrasing.

        Respond ONLY with a JSON object. Format:
        {{
            "action": "string",
            "urgency": "string",
            "meaning": "string"
        }}
        """

        try:
            # --- Generator Agent (with retry) ---
            gen_response = await retry_with_backoff(
                self.client.models.generate_content,
                model='gemini-2.5-flash',
                contents=generator_prompt,
            )
            raw_result = json.loads(self._strip_markdown(gen_response.text))

            # --- Verifier Agent (with retry) ---
            verifier_prompt = f"""
            You are a Verifier AI checking translation accuracy.
            Review the generated structured meaning against the original text to ensure correctness and no hallucinations.
            Original: "{text}"
            Generated Meaning: {json.dumps(raw_result)}

            Is this translation completely accurate and literal? Only return a JSON object.
            Format:
            {{
                "is_accurate": bool,
                "corrected_meaning": "plain string if needed, else same as meaning",
                "clarity_score": number from 0 to 100
            }}
            """
            ver_response = await retry_with_backoff(
                self.client.models.generate_content,
                model='gemini-2.5-flash',
                contents=verifier_prompt,
            )
            verification = json.loads(self._strip_markdown(ver_response.text))

            return {
                "action": raw_result.get("action", ""),
                "urgency": raw_result.get("urgency", "Low"),
                "meaning": self._extract_meaning(verification, raw_result),
                "clarity_score": verification.get("clarity_score", 80),
            }

        except Exception as e:
            print(f"Error in LLM pipeline translation: {e}")
            return {
                "action": "Error in processing",
                "urgency": "Unknown",
                "meaning": f"Could not translate properly. Error: {str(e)}",
                "clarity_score": 0,
            }


llm_pipeline = LLMPipeline()
