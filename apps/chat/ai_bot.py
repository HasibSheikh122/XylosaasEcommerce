# apps/chat/ai_bot.py
import json
import os
import logging
import re
from openai import OpenAI
from channels.db import database_sync_to_async
from django_tenants.utils import schema_context
from .models import ChatRoom, ChatMessage
from .bot_tools import tool_search_products, tool_get_order_details, tool_get_store_policies

logger = logging.getLogger(__name__)

# ১. মডেলের জন্য ফাংশন ডিক্লারেশন (Function Tools)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "গ্রাহকের রিকোয়ারমেন্ট অনুযায়ী স্টোরের ক্যাটালগ থেকে প্রোডাক্ট সার্চ করা।",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "প্রোডাক্টের নাম বা কিওয়ার্ড (যেমন: মধু, টি-শার্ট, জুতো, তেল)"},
                    "category": {"type": "string", "description": "ক্যাটাগরির নাম"},
                    "max_price": {"type": "number", "description": "সর্বোচ্চ বাজেট"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "গ্রাহকের অর্ডার ট্র্যাকিং ও ডেলিভারি স্ট্যাটাস চেক করা।",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {"type": "string", "description": "অর্ডার আইডি বা নম্বর (যেমন: ORD-1023)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_store_policies",
            "description": "ডেলিভারি সময়, চার্জ, রিটার্ন পলিসি ও পেমেন্ট সম্পর্কিত নিয়মাবলী।",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "enum": ["delivery", "return_policy", "payment_methods", "general"]}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_human_handover",
            "description": "গ্রাহক যদি সরাসরি মানুষের সাথে কথা বলতে চায় বা বট সমাধান করতে না পারে।",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

def get_ai_client_and_model():
    """OpenAI অথবা Groq-এর অ্যাক্টিভ ক্লায়েন্ট ও মডেল নির্ধারণ"""
    api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    configured_model = os.getenv("AI_MODEL_NAME", "").strip()

    if not api_key or api_key == "YOUR_OPENAI_OR_GROQ_API_KEY":
        return None, None

    # Groq API ব্যবহার করলে
    if api_key.startswith("gsk_") or "groq.com" in base_url:
        base_url = base_url or "https://api.groq.com/openai/v1"
        model = configured_model or "llama-3.3-70b-versatile"
    else:
        # ডিফল্ট OpenAI
        base_url = base_url or "https://api.openai.com/v1"
        model = configured_model or "gpt-4o-mini"

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, model


def local_smart_fallback(incoming_text, schema_name, store_name):
    """API না থাকলে বা কোটা শেষ হলেও স্বয়ংক্রিয়ভাবে ডাটাবেস থেকে বুদ্ধিদীপ্ত উত্তর তৈরি"""
    text_lower = incoming_text.lower().strip()

    # ১. শুভেচ্ছা বার্তা
    if any(greet in text_lower for greet in ["hi", "hello", "hey", "salam", "সালাম", "হ্যালো", "কেমন আছো", "kemon aso"]):
        return f"সালাম ও শুভ দিন! '{store_name}'-এর ভার্চুয়াল অ্যাসিস্ট্যান্ট হিসেবে আপনাকে স্বাগতম। আমি কীভাবে আপনাকে সাহায্য করতে পারি?"

    # ২. ডেলিভারি বা পলিসি সম্পর্কিত প্রশ্ন
    if any(w in text_lower for w in ["delivery", "charge", "shipping", "ডেলিভারি", "রিটার্ন", "পেমেন্ট", "টাকা", "payment"]):
        policies = tool_get_store_policies(schema_name)
        return (
            f"🚚 **ডেলিভারি ও পেমেন্ট পলিসি:**\n"
            f"• ডেলিভারি: {policies.get('delivery')}\n"
            f"• পেমেন্ট: {policies.get('payment_methods')}\n"
            f"• রিটার্ন: {policies.get('return_policy')}"
        )

    # ৩. ডাটাবেসে প্রোডাক্ট খোঁজা
    clean_query = re.sub(r'[^\w\s]', '', text_lower)
    search_res = tool_search_products(schema_name, query=clean_query[:25])
    if search_res.get("status") == "success" and search_res.get("products"):
        prods = search_res["products"]
        res_text = f"আমাদের স্টোরে আপনার পছন্দের পণ্যগুলো দেখুন:\n\n"
        for p in prods:
            res_text += f"• **{p['name']}** - {p['price']} (স্টক: {'আছে' if p['in_stock'] else 'স্টক আউট'})\n"
        res_text += "\nপণ্যটির ডিটেইলস দেখতে ব্রাউজ করুন অথবা আমাকে জানান।"
        return res_text

    # ৪. জেনেরিক নিরাপদ ফলব্যাক
    return (
        f"ধন্যবাদ আপনার মেসেজের জন্য! আমি আপনার বার্তাটি পেয়েছি। "
        f"আপনি নির্দিষ্ট কোনো প্রোডাক্ট, ডেলিভারি চার্জ বা অর্ডার ট্র্যাকিং জানতে চাইলে আমাকে লিখে জানাতে পারেন।"
    )


class EnterpriseAIBot:
    @staticmethod
    @database_sync_to_async
    def generate_ai_reply(room_id, customer_id, incoming_text, schema_name):
        with schema_context(schema_name):
            room = ChatRoom.objects.select_related('merchant', 'customer').filter(id=room_id).first()
            if not room:
                return None

            store_name = schema_name.capitalize()
            final_reply = None

            # ১. আগের মেসেজ লোড (শেষ ৫টি মেসেজ, যাতে ডুপ্লিকেট না হয়)
            past_messages = ChatMessage.objects.filter(room=room).order_by('-created_at')[1:6]
            history = []
            for m in reversed(past_messages):
                role = "assistant" if m.sender_id == room.merchant_id else "user"
                if m.text:
                    history.append({"role": role, "content": m.text})

            # ২. ক্লায়েন্ট এবং মডেল চেক
            client, model_name = get_ai_client_and_model()

            if client:
                system_prompt = (
                    f"You are the friendly, intelligent customer support bot for '{store_name}'. "
                    "Answer in Bengali or English based on the customer's input. "
                    "Be polite, concise, and helpful. "
                    "Use provided tools to search products, track orders, or view store policies. "
                    "Never invent product prices without tools."
                )

                messages = [{"role": "system", "content": system_prompt}] + history
                messages.append({"role": "user", "content": incoming_text})

                try:
                    # প্রথম কল: মডেল টুল কল করবে কি না
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        tools=TOOLS_SCHEMA,
                        tool_choice="auto",
                        temperature=0.3
                    )

                    choice = response.choices[0].message
                    tool_calls = choice.tool_calls

                    if tool_calls:
                        # সেইফ ডিকশনারি রূপান্তর (Groq ও OpenAI উভয় প্ল্যাটফর্মেই শতভাগ সাপোর্ট)
                        assistant_msg = {
                            "role": "assistant",
                            "content": choice.content or "",
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments
                                    }
                                }
                                for tc in tool_calls
                            ]
                        }
                        messages.append(assistant_msg)

                        for tool_call in tool_calls:
                            function_name = tool_call.function.name
                            args = json.loads(tool_call.function.arguments or "{}")

                            tool_result = {}
                            if function_name == "search_products":
                                tool_result = tool_search_products(
                                    schema_name=schema_name,
                                    query=args.get("query"),
                                    category=args.get("category"),
                                    max_price=args.get("max_price")
                                )
                            elif function_name == "get_order_details":
                                tool_result = tool_get_order_details(
                                    schema_name=schema_name,
                                    customer_id=customer_id,
                                    order_number=args.get("order_number")
                                )
                            elif function_name == "get_store_policies":
                                tool_result = tool_get_store_policies(schema_name=schema_name)
                            elif function_name == "request_human_handover":
                                tool_result = {"status": "handover", "message": "Store merchant is being notified."}

                            messages.append({
                                "tool_call_id": tool_call.id,
                                "role": "tool",
                                "name": function_name,
                                "content": json.dumps(tool_result, ensure_ascii=False)
                            })

                        second_response = client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            temperature=0.3
                        )
                        final_reply = second_response.choices[0].message.content
                    else:
                        final_reply = choice.content

                except Exception as e:
                    # আসল এরর টার্মিনালে প্রিন্ট করা
                    print(f"\n❌ [AI BOT API ERROR]: {type(e).__name__} -> {e}\n")
                    logger.error(f"AI Bot Exception: {e}")
                    # API ক্র্যাশ করলেও লোকাল ডাটাবেস থেকে সঠিক রিপ্লাই দেবে
                    final_reply = local_smart_fallback(incoming_text, schema_name, store_name)
            else:
                # API কী না থাকলে সরাসরি লোকাল ডাটাবেস হ্যান্ডলার
                final_reply = local_smart_fallback(incoming_text, schema_name, store_name)

            # ৩. বটের মেসেজটি ডাটাবেসে সেভ করা
            bot_sender = room.merchant
            msg = ChatMessage.objects.create(
                room=room,
                sender=bot_sender,
                text=final_reply,
                message_type='text'
            )

            return {
                'id': msg.id,
                'room': room.id,
                'sender': bot_sender.id,
                'sender_id': bot_sender.id,
                'sender_details': {
                    'id': bot_sender.id,
                    'name': f"{store_name} AI Assistant",
                    'email': bot_sender.email
                },
                'text': msg.text,
                'file_url': None,
                'file_name': None,
                'file_size': None,
                'message_type': 'text',
                'created_at': msg.created_at.isoformat()
            }