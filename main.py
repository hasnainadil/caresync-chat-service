import os
from typing import Annotated, List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import date, datetime
from tools import hospital_search_tool
from tools import get_test_by_id_tool, get_tests_by_type_tool, get_tests_by_hospital_tool
import threading
from enum import Enum

# enums Roles:


class Roles(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageResponse(BaseModel):
    content: str
    id: str
    role: str
    createdAt: str


# --- FastAPI Setup ---
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# --- User Message Store ---
user_messages: Dict[str, List] = {}
user_lock = threading.Lock()

# --- LLM and Tools Setup ---
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
llm_with_tools = llm.bind_tools([
    hospital_search_tool,
    get_test_by_id_tool,
    get_tests_by_type_tool,
    get_tests_by_hospital_tool
])

# --- Request/Response Models ---


class ChatRequest(BaseModel):
    userId: str
    message: str
    role: str = Roles.USER.value
    createdAt: str


class ChatResponse(BaseModel):
    response: str


# --- Chat Endpoint ---
SYSTEM_PROMPT = '''
You are a helpful assistant for a hospital information website. You can answer questions about hospitals and medical tests by calling the provided tools. If a user asks for information about hospitals, types, costs, or tests, use the tools to fetch real data. Otherwise, answer conversationally.

Guidelines:
- Always use the available tools to answer questions about hospitals, medical tests, costs, types, or locations.
- If the user asks for a hospital or test by type, cost, or other criteria, use the search tool with the most relevant filters.
- If the user input contains typos or ambiguous terms, try to match them to the closest valid enum value.
- If the user asks a general question or for advice, answer conversationally.
- If a user asks for a list, provide a concise summary (e.g., hospital name, type, cost, city).
- If a user asks for details, provide the most relevant details from the tool response.

Available HOSPITAL_TYPE enum values:
- PUBLIC: Government-owned hospitals
- PRIVATE: Privately-owned hospitals
- GENERAL: General medical hospitals
- SPECIALIZED: Specialized medical hospitals
- CHILDREN: Pediatric hospitals
- MATERNITY: Maternity hospitals
- RESEARCH: Research hospitals
- REHABILITATION: Rehabilitation centers

Available COST_RANGE enum values:
- VERY_LOW: Very affordable hospitals
- LOW: Low-cost hospitals
- MODERATE: Moderately-priced hospitals
- HIGH: High-cost hospitals
- VERY_HIGH: Premium hospitals

Available TEST_TYPE enum values:
- BLOOD: Blood-related tests
- HEART: Cardiac tests
- BRAIN: Neurological tests
- LUNG: Pulmonary tests
- EYE: Ophthalmological tests
- BONE: Orthopedic tests
- SKIN: Dermatological tests
- GENERAL: General medical tests
- LIVER: Hepatic tests
- KIDNEY: Renal tests

If you are unsure about a user request, ask clarifying questions.
'''


@app.post("/chat/v1/send", status_code=200, response_model=MessageResponse)
async def chat_endpoint(request: ChatRequest):
    userId = request.userId
    message = request.message
    with user_lock:
        if userId not in user_messages:
            user_messages[userId] = [SystemMessage(content=SYSTEM_PROMPT)]
        messages = user_messages[userId]
    # Add user message
    messages.append(HumanMessage(content=message))
    # Model call
    ai_msg = llm_with_tools.invoke(messages)
    print(ai_msg)
    messages.append(ai_msg)
    # Tool call loop
    tool_calls = getattr(ai_msg, 'tool_calls', [])
    tool_dict = {
        "hospital_search": hospital_search_tool,
        "get_test_by_id": get_test_by_id_tool,
        "get_tests_by_type": get_tests_by_type_tool,
        "get_tests_by_hospital_name_or_id": get_tests_by_hospital_tool,
    }
    while tool_calls and len(tool_calls) > 0:
        for tool_call in tool_calls:
            tool_name = tool_call["name"].lower()
            selected_tool = tool_dict.get(tool_name)
            if selected_tool is not None:
                tool_msg = selected_tool.invoke(tool_call)
                messages.append(tool_msg)
        ai_msg = llm_with_tools.invoke(messages)
        messages.append(ai_msg)
        tool_calls = getattr(ai_msg, 'tool_calls', [])
    # Save updated messages
    with user_lock:
        user_messages[userId] = messages
    # Return last AI message content
    return MessageResponse(content=messages[-1].content, id=f"{userId}_assistant_{len(messages)}", role=Roles.ASSISTANT.value, createdAt=datetime.now().isoformat())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
