import httpx
from app.core.config import settings
from app.models.message import Message
from app.services.twitter import TwitterService


class AIService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        self.twitter = TwitterService()  # ✅ Initialize Twitter service

    async def generate_response(self, message: Message, custom_prompt: str = None) -> str:
        """
        Generate an AI response for a given message using OpenAI GPT-4
        """
        try:
            # Default prompt for professional social media handling
            default_prompt = """You are a professional social media handler for a company. Your role is to respond to customer inquiries and mentions on social media platforms in a friendly, helpful, and professional manner.

Guidelines for your responses:
1. Always greet the user warmly first
2. Be concise but informative (keep responses under 280 characters for Twitter)
3. Maintain a professional yet friendly tone
4. If you don't have enough information to help, politely ask for more details
5. Always end with a helpful closing or next step
6. Use appropriate emojis sparingly to add warmth

User's message: {message_text}

Generate a professional response:"""

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

    # 🧠 NEW: Handle Twitter mentions automatically
    async def handle_twitter_mention(self, access_token: str, mention):
        """
        Fetch conversation context, generate an AI response, and reply to the mention.
        """
        try:
            # 1️⃣ Fetch conversation context (the thread memory)
            context = await self.twitter.fetch_conversation_context(
                access_token,
                conversation_id=mention["conversation_id"]
            )

            # Combine all previous messages with the current one
            full_context = "\n".join(context + [mention["text"]])

            # 2️⃣ Send the entire context to GPT
            prompt = f"""
You are an AI social media assistant replying to a mention in a conversation thread.

Here’s the full thread context:
{full_context}

Respond naturally to the latest message (the last one). Be concise (under 280 chars) and keep a friendly, professional tone.
"""
            response = await self.generate_custom_response(
                message_text=mention["text"],
                custom_prompt=prompt
            )

            # 3️⃣ Reply back on Twitter
            await self.twitter.reply_to_tweet(
                access_token,
                tweet_id=mention["id"],
                text=response
            )

            print(f"✅ Responded to mention @{mention['author_id']} with: {response}")
            return response

        except Exception as e:
            print(f"❌ Error handling mention: {e}")
            return None

    # 🌀 Optional: Automatically handle all mentions
    async def handle_all_mentions(self, access_token: str):
        """
        Fetch all new mentions and reply intelligently to each.
        """
        mentions = await self.twitter.fetch_mentions(access_token)
        for mention in mentions:
            await self.handle_twitter_mention(access_token, mention)
