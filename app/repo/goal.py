from app.models._mixin import BaseMixin
from app.models.goal import Goal


class GoalRepo(BaseMixin[Goal]):
    ...


goal_repo = GoalRepo(Goal)
