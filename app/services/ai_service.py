import httpx
from app.core.config import settings
from app.models.message import Message


class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
    
    async def generate_response(self, message: Message, custom_prompt: str = None) -> str:
        """
        Generate an AI response for a given message using OpenAI GPT-4
        """
        try:
            # Default prompt for professional social media handling
            default_prompt = """You are an expert AI assistant designed to manage the X (formerly Twitter) replies for the handle of a Nigerian commercial bank called Sterling Bank. Your primary goal is to provide valuable, constructive, and highly relevant feedback or solutions to followers' questions, comments, or problems.

Tone and Style Constraints:

Professional, Helpful, and Enthusiastic.

Concise: Keep the response under 280 characters (the X limit).

Actionable: Focus on providing a concrete solution, resource, or next step.

Avoid: Generic phrases like "That's a great question" or overly simple acknowledgments.

Context & Input
The user's original message is provided below. You must analyze the message to identify the core problem, request, or comment.

USER MESSAGE:

{message_text}

Task Instructions (Step-by-Step)
Analyze and Classify: Quickly classify the user's message intent (e.g., Question about X, Feedback on Product Y, Problem with Service Z, General Comment).

Determine Value Proposition: Identify the best possible form of assistance that can fit into a concise X response (e.g., Provide a specific code snippet, Link to a precise documentation page, Suggest a troubleshooting step, Offer a counter-argument/solution).

Draft Response: Write the response, ensuring it directly addresses the user's need.

Start with a personal address (if possible, without exceeding length limits, though a simple, direct tone is often better).

Include the most critical piece of information first.

Crucially, format any resource or link in a way that minimizes character count.

Example (Internal Reasoning and Output Format)
Example Input: "I'm having trouble implementing exponential backoff in Python for your API. My script keeps hitting 429 errors!"

Parameter	Internal Reasoning
Intent	Technical Problem/Support Request (Rate Limiting)
Value	Provide a link to the exact documentation or a brief, correct code structure(if available).
Response Draft	Hi! For 429s, use the X-Rate-Limit-Reset header. Implement exponential backoff with a max delay of 30s. The full guide is here: [LINK_TO_DOCS(IF Available)]

Always follow this response format:

Hi, <response message>
"""

            # Use custom prompt if provided, otherwise use default
            prompt = custom_prompt if custom_prompt else default_prompt.format(message_text=message.text)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a professional social media handler. Respond to customer inquiries in a friendly, helpful, and professional manner. Keep responses concise and under 280 characters."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 150,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.json()}")
                
                result = response.json()
                generated_text = result['choices'][0]['message']['content'].strip()
                
                return generated_text
                
        except Exception as e:
            raise Exception(f"Failed to generate AI response: {str(e)}")
    
    async def generate_custom_response(self, message_text: str, custom_prompt: str) -> str:
        """
        Generate an AI response with a custom prompt
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {
                                "role": "user",
                                "content": f"{custom_prompt}\n\nUser's message: {message_text}"
                            }
                        ],
                        "max_tokens": 200,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.json()}")
                
                result = response.json()
                generated_text = result['choices'][0]['message']['content'].strip()
                
                return generated_text
                
        except Exception as e:
            raise Exception(f"Failed to generate custom AI response: {str(e)}")
