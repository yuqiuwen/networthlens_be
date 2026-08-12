
from app.core.exception import APIException
from app.repo.category import category_repo
from app.schemas.category import CategoryQuerySchema, CreateCategorySchema, UpdateCategorySchema
from app.utils.common import gen_ulid


class CategoryService:
    async def create(
        self,
        session,
        cur_user,
        data: CreateCategorySchema,
    ):
        exists = await category_repo.exists_name(
            session,
            cur_user.id,
            data.category_type,
            data.name,
        )

        if exists:
            raise APIException(
                errmsg="分类名称已存在",
            )

        category = await category_repo.create(
            session,
            {
                "id": gen_ulid(),
                "user_id": cur_user.id,
                **data.model_dump(),
            },
        )

        return category.id

    async def list(
        self,
        session,
        cur_user,
        query: CategoryQuerySchema,
    ):
        return await category_repo.list_by_user(
            session,
            cur_user.id,
            category_type=query.category_type,
        )

    async def update(
        self,
        session,
        cur_user,
        category_id: str,
        data: UpdateCategorySchema,
    ):
        category = await category_repo.get_detail(
            session,
            category_id,
            cur_user.id,
        )

        if not category:
            raise APIException(errmsg="分类不存在")

        if category.user_id is None:
            raise APIException(errmsg="系统分类不可修改")

        payload = data.model_dump(exclude_unset=True)

        if "name" in payload:
            exists = await category_repo.exists_name(
                session,
                cur_user.id,
                category.category_type,
                payload["name"],
                exclude_id=category_id,
            )

            if exists:
                raise APIException(errmsg="分类名称已存在")

        await category_repo.update(
            session,
            category,
            payload,
        )

        return True

    async def delete(
        self,
        session,
        cur_user,
        category_id: str,
    ):
        category = await category_repo.get_detail(
            session,
            category_id,
            cur_user.id,
        )

        if not category:
            raise APIException(errmsg="分类不存在")

        if category.user_id is None:
            raise APIException(errmsg="系统分类不可删除")

        child_count = await category_repo.count_children(
            session,
            category_id,
        )

        if child_count:
            raise APIException(errmsg="存在子分类，无法删除")

        await category_repo.soft_delete(
            session,
            category_id,
        )

        return True


