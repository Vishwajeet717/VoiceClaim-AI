import json

from datetime import date

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from agent.conversation_manager import (
    get_next_conversation_response,
    process_customer_message,
)

from agent.state import create_initial_claim_state

from rag.answer import answer_policy_question


app = FastAPI(
    title="VoiceClaim AI"
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "message": "VoiceClaim AI backend is running"
    }


# ============================================================
# POLICY RAG
# ============================================================

class PolicyQuestion(BaseModel):
    question: str
    policy_id: int | None = None


@app.post("/policy/query")
def policy_query(
    request: PolicyQuestion,
):
    return answer_policy_question(
        question=request.question,
        policy_id=request.policy_id,
    )


# ============================================================
# VOICE / TEXT CONVERSATION WEBSOCKET
# ============================================================

@app.websocket("/ws/voice")
async def voice_websocket(
    websocket: WebSocket,
):
    await websocket.accept()

    print()
    print("=" * 70)
    print("[VOICE] Browser connected")
    print("=" * 70)

    # One ClaimState per call.
    claim_state = create_initial_claim_state()

    try:

        while True:

            raw_message = (
                await websocket.receive_text()
            )

            payload = json.loads(
                raw_message
            )

            message_type = payload.get(
                "type"
            )

            # ====================================================
            # CUSTOMER TEXT
            # ====================================================

            if message_type == "text":

                customer_message = (
                    payload
                    .get("text", "")
                    .strip()
                )

                if not customer_message:
                    continue

                print()
                print("=" * 70)
                print("[VOICE] CUSTOMER")
                print("=" * 70)
                print(customer_message)

                try:

                    # ------------------------------------------------
                    # Voice/text → ClaimState
                    # ------------------------------------------------

                    await websocket.send_json(
                        {
                            "type":
                                "agent_processing"
                        }
                    )

                    claim_state = (
                        process_customer_message(
                            state=claim_state,
                            message=customer_message,
                            reference_date=date.today(),
                        )
                    )

                    print(
                        "[VOICE] Intent:",
                        claim_state.get(
                            "current_intent"
                        ),
                    )

                    print(
                        "[VOICE] Next step:",
                        claim_state.get(
                            "next_step"
                        ),
                    )

                    print(
                        "[VOICE] Missing:",
                        claim_state.get(
                            "missing_information",
                            [],
                        ),
                    )

                    print(
                        "[VOICE] Contradictions:",
                        claim_state.get(
                            "contradictions",
                            [],
                        ),
                    )

                    # ------------------------------------------------
                    # ClaimState → response
                    # ------------------------------------------------

                    agent_response = (
                        get_next_conversation_response(
                            claim_state
                        )
                    )

                    print()
                    print(
                        "[VOICE] VOICECLAIM"
                    )
                    print(
                        agent_response
                    )

                    # Save latest response.
                    claim_state["tool_results"] = {
                        **claim_state.get(
                            "tool_results",
                            {},
                        ),
                        "last_agent_response":
                            agent_response,
                    }

                    # ------------------------------------------------
                    # Send response to browser
                    # ------------------------------------------------

                    await websocket.send_json(
                        {
                            "type":
                                "agent_response",

                            "text":
                                agent_response,

                            "next_step":
                                claim_state.get(
                                    "next_step"
                                ),

                            "intent":
                                claim_state.get(
                                    "current_intent"
                                ),
                        }
                    )

                except Exception as exc:

                    print()
                    print(
                        "[VOICE ERROR]"
                    )
                    print(
                        repr(exc)
                    )

                    await websocket.send_json(
                        {
                            "type":
                                "error",

                            "message":
                                str(exc),
                        }
                    )

            # ====================================================
            # END SESSION
            # ====================================================

            elif message_type == "stop":

                print(
                    "[VOICE] Session ended by browser"
                )

                break

            # ====================================================
            # PING
            # ====================================================

            elif message_type == "ping":

                await websocket.send_json(
                    {
                        "type":
                            "pong"
                    }
                )

    except WebSocketDisconnect:

        print(
            "[VOICE] Browser disconnected"
        )

    except Exception as exc:

        print()
        print(
            "[VOICE ERROR]"
        )
        print(
            repr(exc)
        )

        try:

            await websocket.send_json(
                {
                    "type":
                        "error",

                    "message":
                        str(exc),
                }
            )

        except Exception:
            pass

    finally:

        print(
            "[VOICE] Voice session closed"
        )