from app.core.loggers import app_logger
from fastapi.requests import HTTPConnection
from fastapi.security.utils import get_authorization_scheme_param
from starlette.authentication import AuthCredentials, AuthenticationBackend, AuthenticationError
from fastapi import Request

from app.config import settings
from app.core.app_code import AppCode
from app.core.exception import AuthException
from app.core.http_handler import make_json_response, make_response
from app.ext.jwt import TokenUserInfo, jwt_manager


class _AuthenticationError(AuthenticationError):
    """重写内部认证错误类"""

    def __init__(
        self,
        *,
        code: int = AppCode.AUTH_ERROR,
        msg: str = "Auth Exception",
        errmsg: str = "认证异常",
    ) -> None:
        """
        初始化认证错误

        :param code: 错误码
        :param msg: 错误信息
        :param headers: 响应头
        :return:
        """
        self.code = code
        self.msg = msg
        self.errmsg = errmsg


class JwtAuthMiddleware(AuthenticationBackend):
    """JWT 认证中间件"""

    @staticmethod
    def auth_exception_handler(conn: HTTPConnection, exc: _AuthenticationError):
        """
        覆盖内部认证错误处理

        :param conn: HTTP 连接对象
        :param exc: 认证错误对象
        :return:
        """
        return make_json_response(exc.msg, code=exc.code, errmsg=exc.errmsg)

    @staticmethod
    async def jwt_authentication(token: str) -> TokenUserInfo:
        """
        JWT 认证

        :param token: JWT token
        :return:
        """
        try:
            token_payload = jwt_manager.verify_token(token)
            if token_payload.flg != jwt_manager.config.AC_TOKEN_KEY:
                raise _AuthenticationError(
                    code=AppCode.AUTH_INVALID,
                    msg="invalid token type",
                    errmsg="身份凭证无效",
                )
            return await jwt_manager.load_from_cache(
                token_payload.user_id,
                token_payload.jti,
                token_payload.flg,
            )
        except _AuthenticationError:
            raise
        except AuthException as e:
            raise _AuthenticationError(
                code=e.code,
                msg=e.message,
                errmsg=e.errmsg,
            ) from e
        except Exception as e:
            app_logger.error(str(e))
            raise _AuthenticationError(
                code=AppCode.INTERNAL_ERROR,
                msg="server error!",
                errmsg="系统异常",
            ) from e


    async def authenticate(self, request: Request) -> tuple[AuthCredentials, TokenUserInfo] | None:
        """
        认证请求

        :param request: FastAPI 请求对象
        :return:
        """

        path = request.url.path

        # 白名单
        if path in settings.WHITE_ROUTE_LIST:
            return None

        for pattern in settings.WHITE_ROUTE_PATTERN:
            if pattern.match(path):
                return None

        authorization = request.headers.get("Authorization")
        if not authorization:
            return None

        scheme, token = get_authorization_scheme_param(authorization)

        if scheme.lower() != "bearer":
            return None

        user = await self.jwt_authentication(token)

        return AuthCredentials(["authenticated"]), user

    # async def authenticate_all(self, request: Request) -> tuple[AuthCredentials, TokenUserInfo] | None:
    #     """
    #     全局鉴权

    #     :param request: FastAPI 请求对象
    #     :return:
    #     """
    #     token = request.headers.get("Authorization")
    #     path = request.url.path

    #     if path in settings.WHITE_ROUTE_LIST:
    #         return
    #     for pattern in settings.WHITE_ROUTE_PATTERN:
    #         if pattern.match(path):
    #             return None
    #     if not token:
    #         raise _AuthenticationError(code=AppCode.AUTH_INVALID, msg="token is required", errmsg="未登录")

    #     scheme, token = get_authorization_scheme_param(token)
    #     if scheme.lower() != "bearer":
    #         raise _AuthenticationError(msg="invalid token scheme", errmsg="token scheme invalid")

    #     user = await self.jwt_authentication(token)

    #     return AuthCredentials(["authenticated"]), user
