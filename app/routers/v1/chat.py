from fastapi import Depends
from fastapi.responses import StreamingResponse

from app.routers import BaseAPIRouter
from app.core.http_handler import CursorPageRespModel, make_response, RespModel
from app.core.dependencies import RequireAuthDep, SessionDep
from app.schemas.chat import ChatMessageQuerySchema, ChatReqSchema, ChatRespSchema, AIChatMessageSchema, AIChatSessionSchema, ChatStreamEvent, CreateChatSessionSchema
from app.services.agent.chat import AgentChatService
from app.services.agent.message import MessageService as AgentMessageService
from app.services.agent.session import AgentSessionService



router = BaseAPIRouter(prefix="/chat", tags=["AI助手"])


async def sse_wrapper(generator):
    async for event in generator:
        yield f"data: {ChatStreamEvent.model_validate(event).model_dump_json()}\n\n"

    yield "event: done\ndata: [DONE]\n\n"


@router.post(
    "",
    summary="聊天",
    response_model=RespModel[ChatRespSchema],
)
async def chat(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: ChatReqSchema,
):
    service = AgentChatService(cur_user)

    result = await service.chat(
        session=session,
        message=data.message,
        session_id=data.session_id,
    )

    return make_response(data=ChatRespSchema.model_validate(result))


@router.post(
    "/stream",
    summary="流式聊天",
)
async def stream_chat(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: ChatReqSchema,
):

    service = AgentChatService(cur_user)
    return StreamingResponse(
        sse_wrapper(
            service.stream_chat(
                session=session,
                session_id=data.session_id,
                message=data.message,
            )
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



@router.post(
    "/sessions",
    summary="创建会话",
    response_model=RespModel[AIChatSessionSchema],
)
async def create_session(
    session: SessionDep,
    cur_user: RequireAuthDep,
    data: CreateChatSessionSchema,
):
    service = AgentSessionService()

    result = await service.create(
        session=session,
        cur_user=cur_user,
        title=data.title,
    )

    return make_response(data=result)


@router.get(
    "/sessions",
    summary="会话列表",
    response_model=RespModel[list[AIChatSessionSchema]],
)
async def session_list(
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    service = AgentSessionService()

    result = await service.list(
        session=session,
        cur_user=cur_user,
    )

    return make_response(data=result)


@router.get(
    "/sessions/{session_id}",
    summary="会话详情",
    response_model=RespModel[AIChatSessionSchema],
)
async def session_detail(
    session_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    service = AgentSessionService()

    result = await service.detail(
        session=session,
        cur_user=cur_user,
        session_id=session_id,
    )

    return make_response(data=result)


@router.delete(
    "/sessions/{session_id}",
    summary="删除会话",
    response_model=RespModel[bool],
)
async def delete_session(
    session_id: str,
    session: SessionDep,
    cur_user: RequireAuthDep,
):
    service = AgentSessionService()

    result = await service.delete(
        session=session,
        cur_user=cur_user,
        session_id=session_id,
    )

    return make_response(data=result)


@router.get(
    "/sessions/{session_id}/messages",
    summary="消息列表",
    response_model=CursorPageRespModel[AIChatMessageSchema],
)
async def message_list(
    session: SessionDep,
    cur_user: RequireAuthDep,
    params: ChatMessageQuerySchema = Depends(),
):
    service = AgentMessageService()

    result = await service.list(
        session=session,
        cur_user=cur_user,
        params=params,
    )

    return make_response(data=result)
