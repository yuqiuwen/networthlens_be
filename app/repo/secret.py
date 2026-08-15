from app.constant import UserSecretCode
from app.models.secret import UserSecretsModel
from app.models._mixin import BaseMixin
from app.utils.common import gen_ulid


class SecretRepo(BaseMixin[UserSecretsModel]):
    async def get_default(self, session, user_id: int):
        return await self.filter_one(
            session,
            self.model.user_id == user_id,
            self.model.code == UserSecretCode.DEFAULT.value,
        )

    async def set_default(self, session, user_id: int, code: str):
        secret = await self.get_default(session, user_id)
        if secret is None:
            secret = UserSecretsModel(
                id=gen_ulid(),
                user_id=user_id,
                code=UserSecretCode.DEFAULT.value,
            )

        secret.secret = code
        return await self.save(session, secret)

    async def delete_default(self, session, user_id: int) -> bool:
        secret = await self.get_default(session, user_id)
        if secret is None:
            return False
        await self.delete_instance(session, secret)
        return True


secret_repo = SecretRepo(UserSecretsModel)
