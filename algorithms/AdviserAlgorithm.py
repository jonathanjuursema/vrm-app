from itertools import chain
from functools import lru_cache, cmp_to_key

from ApplicationContext import ApplicationContext

from pandas import DataFrame


class AdviserAlgorithm:
    ua = None
    pa = None

    users = None
    perms = None
    roles = None
    roles_count = None

    sorted_users = None
    sorted_perms = None

    application_context = None

    pseudo = False

    def __init__(self, application_context: ApplicationContext):
        self.ua = application_context.role_data.user_assignment
        self.pa = application_context.role_data.permission_assignment
        self.users = application_context.role_data.user_names
        self.perms = application_context.role_data.permission_names
        self.roles = application_context.role_data.roles
        self.roles_count = application_context.role_data.roles_count

        self.pseudo = True

        self.application_context = application_context

    def execute(self):
        self.application_context.stage = 5
        self.sorted_users = list(chain(*self.sort_set(users=True)))
        self.sorted_perms = list(chain(*self.sort_set(permissions=True)))

    def sort_set(self, users=False, permissions=False):
        self.application_context.stage_percentage = "Making itemsets for {}...".format(
            'users' if users else 'permissions')
        item_sets = self.make_item_sets(users=users, permissions=permissions)

        self.application_context.stage_percentage = "Sorting {} itemsets for {}...".format(len(item_sets),
                                                                                           'users' if users else 'permissions')
        item_sets = sorted(item_sets, key=cmp_to_key(self.itemset_position_sort_comp), reverse=True)
        sorted_items = []

        item_sets_done = 0
        for item_set in item_sets:
            if len(sorted_items) < 2:
                sorted_items.append(item_set)
            else:
                jacc_first = self.jacc_function(item_set, sorted_items[0], users=users, permissions=permissions)
                jacc_last = self.jacc_function(item_set, sorted_items[-1], users=users, permissions=permissions)
                if jacc_first > jacc_last:
                    p = 0
                    j = jacc_first
                else:
                    p = len(sorted_items)
                    j = jacc_last

                for i in range(1, len(sorted_items)):
                    j_prec = self.jacc_function(item_set, sorted_items[i - 1], users=users, permissions=permissions)
                    j_succ = self.jacc_function(item_set, sorted_items[i], users=users, permissions=permissions)
                    j_curr = self.jacc_function(sorted_items[i - 1], sorted_items[i], users=users,
                                                permissions=permissions)

                    if max(j_prec, j_succ) > j and min(j_prec, j_succ) >= j_curr:
                        p = i
                        j = max(j_prec, j_succ)

                sorted_items.insert(p, item_set)

            item_sets_done += 1
            self.application_context.stage_percentage = "Optimising {} {} ({}%)...".format(
                len(item_sets),
                'users' if users else 'permissions',
                int((item_sets_done / len(item_sets)) * 100)
            )

        return [i[0] for i in sorted_items]

    def make_item_sets(self, users=False, permissions=False):

        item_sets = {}

        if users is True:
            items = self.ua
        elif permissions is True:
            items = self.pa
        else:
            raise Exception("Either users or permissions should be true.")

        for item in range(0, items.shape[0]):

            item_set_roles = []

            for role in range(0, items.shape[1]):
                if items.iloc[item, role]:
                    item_set_roles.append(role)

            item_set_roles = tuple(item_set_roles)

            if item_set_roles in item_sets.keys():
                item_sets[item_set_roles].append(item)
            else:
                item_sets[item_set_roles] = [item]

        item_sets = [(tuple(v), tuple(k)) for k, v in item_sets.items()]

        sorted_item_sets = []

        for idx, item_set in enumerate(item_sets):
            if users is True:
                items = tuple(sorted(item_set[0], key=lambda item: self.user_overlay_weight(item)))
            if permissions is True:
                items = tuple(sorted(item_set[0], key=lambda item: self.perm_overlay_weight(item)))
            sorted_item_sets.append((items, item_set[1]))

        return sorted_item_sets

    @lru_cache(maxsize=10000000)
    def itemset_position_sort_comp(self, item_set_a, item_set_b):
        roles_a = set(item_set_a[1])
        roles_b = set(item_set_b[1])
        complement_1 = roles_a - roles_b
        complement_2 = roles_b - roles_a

        if len(complement_1) == 0 or len(complement_2) == 0:
            return 0

        if self.pseudo:
            max_1 = max([self.prole_frequency(r) for r in complement_1])
            max_2 = max([self.prole_frequency(r) for r in complement_2])
        else:
            max_1 = max([self.ass_users_count(r) * self.ass_perms_count(r) for r in complement_1])
            max_2 = max([self.ass_users_count(r) * self.ass_perms_count(r) for r in complement_2])

        return 1 if max_1 > max_2 else -1

    @lru_cache(maxsize=10000000)
    def jacc_function(self, item_set_a, item_set_b, users=False, permissions=False):

        role_intersection = set(item_set_a[1]).intersection(set(item_set_b[1]))
        role_union = set(item_set_a[1]).union(set(item_set_b[1]))

        if users is True:
            j = sum(
                [self.ass_perms_count(x) * self.prole_frequency(x) if self.pseudo else 1 for x in role_intersection]
            ) / sum(
                [self.ass_perms_count(x) * self.prole_frequency(x) if self.pseudo else 1 for x in role_union]
            )
            return j
        elif permissions is True:
            j = sum(
                [self.ass_users_count(x) * self.prole_frequency(x) if self.pseudo else 1 for x in role_intersection]
            ) / sum(
                [self.ass_users_count(x) * self.prole_frequency(x) if self.pseudo else 1 for x in role_union]
            )
            return j
        else:
            raise Exception("Either users or permissions should be true.")

    @lru_cache(maxsize=10000000)
    def prole_frequency(self, role):
        return self.roles_count[role]

    @lru_cache(maxsize=10000000)
    def ass_users_count(self, role):
        return list(self.ua.iloc[:, role].values).count(True)

    @lru_cache(maxsize=10000000)
    def ass_perms_count(self, role):
        return list(self.pa.iloc[:, role].values).count(True)

    @lru_cache(maxsize=10000000)
    def user_overlay_weight(self, user):
        if self.application_context.overlay_up is None:
            return 0
        name = self.users[user]
        values = list(self.application_context.overlay_up.loc[name].values)
        return sum(values) / len(values)

    @lru_cache(maxsize=10000000)
    def perm_overlay_weight(self, permission):
        if self.application_context.overlay_up is None:
            return 0
        name = self.perms[permission]
        values = list(self.application_context.overlay_up[name].values)
        return sum(values) / len(values)

    @lru_cache(maxsize=10000000)
    def get_sorted_sets(self):
        return self.sorted_users, self.sorted_perms

    def get_sorted_up(self, up):
        sorted_sets = self.get_sorted_sets()
        return up[[self.perms[p] for p in sorted_sets[1]]].reindex([self.users[u] for u in sorted_sets[0]])

    def get_sorted_overlay(self, overlay):
        sorted_sets = self.get_sorted_sets()
        return overlay[[self.perms[p] for p in sorted_sets[1]]].reindex([self.users[u] for u in sorted_sets[0]])

    def print_sorted_up(self, up):
        sorted_up = self.get_sorted_up(up).replace(to_replace=True, value='X').replace(to_replace=False, value=' ')
        sorted_up.columns = [x.replace('permission_', '') for x in sorted_up.columns]
        print(sorted_up)
