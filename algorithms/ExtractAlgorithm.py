from random import randrange
from pandas import DataFrame, merge
from functools import lru_cache
from application import ApplicationContext


class ExtractAlgorithm:
    up = None
    pseudo_roles = None
    pseudo_roles_count = None
    pseudo_user_assignment = None
    pseudo_permission_assignment = None

    application_context = None

    def __init__(self, application: ApplicationContext):
        self.up = application.working_up
        self.application_context = application

    @lru_cache(maxsize=10000000)
    def users(self, permission):
        u = []
        col = self.up.iloc[:, permission]
        for i, p in enumerate(col):
            if p == 1:
                u.append(i)
        return tuple(u)

    @lru_cache(maxsize=10000000)
    def perms(self, user):
        p = []
        col = self.up.iloc[user, :]
        for i, u in enumerate(col):
            if u == 1:
                p.append(i)
        return tuple(p)

    @lru_cache(maxsize=10000000)
    def pseudo_role(self, user, permission):
        u = self.users(permission)
        p = self.perms(user)
        return u, p

    def execute(self, k):
        shape = self.up.shape
        pseudo_roles = {}
        pseudo_user_assignment = DataFrame(0, index=range(0, shape[0]), columns=[], dtype=bool)
        pseudo_permission_assignment = DataFrame(0, index=range(0, shape[1]), columns=[], dtype=bool)
        count = {}

        for i in range(0, k):
            is_assigned = False

            while not is_assigned:
                # Pick <u, p> from UP uniformly at random
                user = randrange(0, shape[0])
                permission = randrange(0, shape[1])

                if self.up.iloc[user, permission] == 1:
                    is_assigned = True

            # Identify the current pseudo-role
            p = self.pseudo_role(user, permission)

            # Check if pseudo-role has been previously generated
            if p in pseudo_roles:
                pseudo_role_name = pseudo_roles[p]
                # Update frequency of the existing pseudo-role
                count[pseudo_role_name] += 1

            else:
                # Add a new pseudo-role
                pseudo_role_name = len(count.keys())
                pseudo_roles[p] = pseudo_role_name
                count[pseudo_role_name] = 1

                # Update user and permission assignments
                ua = DataFrame(1, index=p[0], columns=[pseudo_role_name], dtype=bool)
                pseudo_user_assignment = merge(pseudo_user_assignment, ua,
                                               left_index=True, right_index=True, how='outer')
                pa = DataFrame(1, index=p[1], columns=[pseudo_role_name], dtype=bool)
                pseudo_permission_assignment = merge(pseudo_permission_assignment, pa,
                                                     left_index=True, right_index=True, how='outer')

            self.application_context.stage_percentage = "{}%".format(int((i / k) * 100))
            self.application_context.stage = 3

        self.pseudo_roles = pseudo_roles
        self.pseudo_roles_count = count
        self.pseudo_user_assignment = pseudo_user_assignment.fillna(False)
        self.pseudo_permission_assignment = pseudo_permission_assignment.fillna(False)

    def get_pseudo_roles(self):
        return self.pseudo_roles

    def get_pseudo_roles_count(self):
        return self.pseudo_roles_count

    def get_pseudo_user_assignment(self):
        return self.pseudo_user_assignment

    def get_pseudo_permission_assignment(self):
        return self.pseudo_permission_assignment

    def get_permission_names(self):
        return list(self.up)

    def get_user_names(self):
        return list(self.up.index)
