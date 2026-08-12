import traceback

from pydantic_ai import AgentRunResultEvent, FinalResultEvent, FunctionToolCallEvent, FunctionToolResultEvent, PartStartEvent, TextPart
from pydantic_ai.messages import PartDeltaEvent, TextPartDelta, ThinkingPartDelta
from app.agent.constant import ChatEventType
from app.agent.context_builder import ContextBuilder
from app.agent.deps import FinAgentDeps
from app.agent.financial_agent import financial_agent
from app.config import settings
from app.ext.jwt import TokenUserInfo
from app.services.agent.message import MessageService as AgentMessageService
from app.services.agent.session import AgentSessionService
from app.core.exception import APIException
from app.services.agent.tool_display import get_tool_display_name, get_tool_running_message
from app.services.fin_analysis import FinancialAnalysisService


class AgentChatService:
    """
    Agent聊天服务

    功能：

    1. 普通聊天
    2. SSE流式聊天
    3. 保存用户消息
    4. 保存Agent消息
    5. 加载历史上下文
    """

    def __init__(self, user: TokenUserInfo):
        self.user = user
        self.default_model = settings.MODEL_CHAT
        self.default_model_provider = settings.LLM_ADAPTER
        self.session_service = AgentSessionService()

        self.message_service = AgentMessageService()

        self.analysis_service = FinancialAnalysisService()

    async def _build_deps(
        self,
        session,
    ):
        return FinAgentDeps(
            session=session,
            user_id=self.user.id,
            analysis_service=self.analysis_service,
            transaction_service=None,
            reminder_service=None,
        )

    async def _load_history(
        self,
        session,
        session_id: str,
    ):
        history = await self.message_service.recent_context(
            session,
            self.user.id,
            session_id,
            limit=20,
        )

        return ContextBuilder.build_messages(history)

    async def _ensure_session(
        self,
        session,
        session_id,
        message,
    ):
        if session_id:
            chat_session = await self.session_service.detail(
                session,
                self.user,
                session_id,
            )

            if not chat_session:
                raise APIException(
                    "会话不存在",
                    code=404,
                )

            return chat_session

        chat_session = await self.session_service.create(
            session=session,
            cur_user=self.user,
            title=message[:30],
        )
        return chat_session

    async def chat(
        self,
        session,
        message: str,
        session_id: str = None,
    ):
        """
        普通聊天
        """

        chat_session = await self._ensure_session(
            session,
            session_id,
            message,
        )

        session_id = chat_session.id

        await self.message_service.create_user_message(
            session,
            self.user.id,
            session_id,
            message,
        )

        message_history = await self._load_history(
            session,
            session_id,
        )

        deps = await self._build_deps(session)

        result = await financial_agent.run(
            message,
            deps=deps,
            message_history=message_history,
        )

        answer = result.output

        assistant_msg = await self.message_service.create_assistant_message(
            session,
            session_id,
            answer,
            user_id=self.user.id,
            model=self.default_model,
            extra_info={
                "provider": self.default_model_provider,
                "model": self.default_model,
            },
        )

        await self.message_service.touch_session(
            session,
            session_id,
        )

        return {
            "session_id": session_id,
            "message_id": assistant_msg.id,
            "answer": result.output,
        }

    async def stream_chat(
        self,
        session,
        message: str,
        session_id: str = None,
    ):
        """
        SSE流式聊天

        返回：

            async generator
        """

        try:
            yield {
                "type": ChatEventType.START,
                "data": {},
            }

            chat_session = await self._ensure_session(
                session,
                session_id,
                message,
            )

            session_id = chat_session.id

            await self.message_service.create_user_message(
                session,
                self.user.id,
                session_id,
                message,
            )

            message_history = await self._load_history(
                session,
                session_id,
            )

            deps = await self._build_deps(session)

            chunks = []

            async with financial_agent.run_stream_events(
                message,
                deps=deps,
                message_history=message_history,
            ) as events:
                async for event in events:

                    # -------------------------
                    # Tool 开始
                    # -------------------------

                    if isinstance(event, FunctionToolCallEvent):
                        part = event.part
                        tool_name = part.tool_name
                        tool_call_id = part.tool_call_id

                        yield {
                            "type": ChatEventType.TOOL_CALL,
                            "data": {
                                "tool_call_id": tool_call_id,
                                "tool_name": tool_name,
                                "display_name": get_tool_display_name(tool_name),
                                "text": get_tool_running_message(tool_name),
                            },
                        }

                        continue


                    # -------------------------
                    # Tool 完成
                    # -------------------------

                    if isinstance(event, FunctionToolResultEvent):
                        yield {
                            "type": ChatEventType.TOOL_RESULT,
                            "data": {
                                "tool_call_id": event.tool_call_id,
                                "tool_name": None,
                                "text": "分析完成",
                            },
                        }

                        continue

                    if isinstance(event, PartStartEvent):
                        if isinstance(event.part, TextPart):
                            if event.part.content:
                                yield {
                                    "type": ChatEventType.CONTENT,
                                    "data": {
                                        "text": event.part.content,
                                    },
                                }

                        continue
                    
                    # -------------------------
                    # LLM 文本增量
                    # -------------------------
                    if isinstance(event, PartDeltaEvent):
                        if isinstance(event.delta, TextPartDelta):
                            if event.delta.content_delta:
                                yield {
                                    "type": ChatEventType.CONTENT,
                                    "data": {
                                        "text": (
                                            event.delta.content_delta
                                        ),
                                    },
                                }

                        elif isinstance(event.delta, ThinkingPartDelta):
                            # 不建议把模型原始思维链直接暴露给用户。
                            #
                            # 前端只收到一个安全的状态事件。
                            yield {
                                "type": ChatEventType.THINKING,
                                "data": {
                                    "message": "正在分析...",
                                },
                            }

                        continue


                    if isinstance(event, FinalResultEvent):
                        # 表示模型已经开始产生最终结果，
                        # 但此时 Agent Run 可能尚未完全结束。
                        continue
                    

                    # -------------------------
                    # Agent 完成
                    # -------------------------
                    if isinstance(event, AgentRunResultEvent):
                        final_result = event.result
                        yield {
                            "type": ChatEventType.FINISH,
                            "data": {
                                "session_id": session_id,
                            },
                        }

                        continue

                if final_result is None:
                    raise APIException(
                        description="AI响应异常",
                        code=500,
                    )


                # async for chunk in result.stream_text(delta=True):
                #     chunks.append(chunk)

                #     yield {
                #         "type": ChatEventType.CONTENT,
                #         "data": {
                #             "text": chunk,
                #         },
                #     }

            # answer = "".join(chunks)
            answer = final_result.output


            assistant_msg = await self.message_service.create_assistant_message(
                session,
                session_id,
                answer,
                user_id=self.user.id,
                model=self.default_model,
                extra_info={
                    "provider": self.default_model_provider,
                    "model": self.default_model,
                    "usage": {
                        "input_tokens": (
                            final_result.usage.input_tokens
                        ),
                        "output_tokens": (
                            final_result.usage.output_tokens
                        ),
                        "requests": (
                            final_result.usage.requests
                        ),
                    },
                },
            )

            yield {
                "type": ChatEventType.FINISH,
                "data": {
                    "session_id": session_id,
                    "message_id": assistant_msg.id,
                },
            }


            await self.message_service.touch_session(
                session,
                session_id,
            )

        except Exception as e:
            traceback.print_exc()
            yield {
                "type": ChatEventType.ERROR,
                "data": {
                    "message": "遇到一点问题了，请稍后重试",
                },
            }


    async def create_session(
        self,
        session,
        title: str | None = None,
    ):
        return await self.session_service.create(
            session,
            self.user,
            title,
        )

    async def session_list(
        self,
        session,
    ):
        return await self.session_service.list(
            session,
            self.user,
        )

    async def session_detail(
        self,
        session,
        session_id: str,
    ):
        return await self.session_service.detail(
            session,
            self.user,
            session_id,
        )

    async def delete_session(
        self,
        session,
        session_id: str,
    ):
        return await self.session_service.delete(
            session,
            self.user,
            session_id,
        )

    async def message_list(
        self,
        session,
        session_id: str,
    ):
        agent_session = await self.session_service.detail(
            session,
            self.user,
            session_id,
        )

        if not agent_session:
            raise APIException(
                errmsg="会话不存在",
                code=404,
            )

        return await self.message_service.list(
            session,
            session_id,
        )
