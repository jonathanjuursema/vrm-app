import pandas
from definitions import ROOT_DIR
import os.path

import pickle
import json


class ApplicationContext(object):
    # Application stages are as follows:
    # 0 - application not initiated
    # 1 - data uploaded but not yet ingested
    # 2 - data ingested; application ready
    # 3 - pseudo role generation
    # 4 - pseudo roles generated
    # 5 - optimisation underway
    # 6 - optimisation done
    stage = None
    stage_percentage = 0

    original_up = None
    working_up = None
    optimised_up = None

    user_meta = None
    permission_meta = None

    overlay_up = None

    role_data = None

    generated_roles = []

    def __init__(self):
        self.stage = 0

        # See if we can load any original data.
        if os.path.isfile('{}/user_data/original_up.csv'.format(ROOT_DIR)):
            print("Detected previously uploaded base file. Ingesting...")
            self.stage = 1
            read_status = self.load_original_data()
            if not read_status:
                self.stage = 0
                try:
                    os.remove('{}/user_data/original_up.csv'.format(ROOT_DIR))
                finally:
                    pass
            else:
                self.stage = 2

        # See if we can load role data.
        if self.stage is 2:
            try:
                role_data = RoleData.from_files(roles_file='{}/user_data/role_data.pkl'.format(ROOT_DIR),
                                                user_assignment_file='{}/user_data/user_assignment.csv'.
                                                format(ROOT_DIR),
                                                permission_assignment_file='{}/user_data/permission_assignment.csv'.
                                                format(ROOT_DIR))
                self.role_data = role_data
                print("Detected previously generated role data. Ingesting...")
                self.stage = 4
            except BaseException:
                try:
                    os.remove('{}/user_data/role_data.pkl'.format(ROOT_DIR))
                except OSError:
                    pass
                try:
                    os.remove('{}/user_data/user_assignment.csv'.format(ROOT_DIR))
                except OSError:
                    pass
                try:
                    os.remove('{}/user_data/permission_assignment.csv'.format(ROOT_DIR))
                except OSError:
                    pass

        # See if we can load optimisation data.
        if self.stage is 4:
            if os.path.isfile('{}/user_data/optimised_up.csv'.format(ROOT_DIR)):
                print("Detected previously generated optimisation file. Ingesting...")
                self.stage = 1
                read_status = self.load_optimised_data()
                if not read_status:
                    self.stage = 5
                    try:
                        os.remove('{}/user_data/optimised_up.csv'.format(ROOT_DIR))
                    finally:
                        pass
                else:
                    self.stage = 6
                    generated_roles_file = '{}/user_data/generated_roles.json'.format(ROOT_DIR)
                    if os.path.isfile(generated_roles_file):
                        with open(generated_roles_file, 'r') as input_file:
                            self.generated_roles = json.load(input_file)
                            print("Detected already existing roles file. Ingesting...")

    def load_original_data(self):
        try:
            self.original_up = pandas.read_csv('{}/user_data/original_up.csv'.format(ROOT_DIR), sep=';', index_col=0)
            self.working_up = pandas.read_csv('{}/user_data/original_up.csv'.format(ROOT_DIR), sep=';', index_col=0)
            if os.path.isfile('{}/user_data/overlay.csv'.format(ROOT_DIR)):
                print("Loading overlay...")
                self.overlay_up = pandas.read_csv('{}/user_data/overlay.csv'.format(ROOT_DIR), sep=';', index_col=0)
            if os.path.isfile('{}/user_data/meta_user.csv'.format(ROOT_DIR)):
                print("Loading user meta data...")
                self.user_meta = pandas.read_csv('{}/user_data/meta_user.csv'.format(ROOT_DIR), sep=';')
            if os.path.isfile('{}/user_data/meta_permission.csv'.format(ROOT_DIR)):
                print("Loading permission meta data...")
                self.permission_meta = pandas.read_csv('{}/user_data/meta_permission.csv'.format(ROOT_DIR), sep=';')
        except (pandas.errors.EmptyDataError, pandas.errors.ParserError):
            return False
        else:
            return True

    def load_optimised_data(self):
        try:
            self.optimised_up = pandas.read_csv('{}/user_data/optimised_up.csv'.format(ROOT_DIR), sep=';', index_col=0)
        except (pandas.errors.EmptyDataError, pandas.errors.ParserError):
            return False
        else:
            return True


class RoleData(object):
    roles = None
    roles_count = None
    user_assignment = None
    permission_assignment = None

    user_names = None
    permission_names = None

    def __init__(self, roles, roles_count, user_names, permission_names, user_assignment, permission_assignment):
        self.roles = roles
        self.roles_count = roles_count
        self.user_names = user_names
        self.permission_names = permission_names
        self.user_assignment = user_assignment
        self.permission_assignment = permission_assignment

    @classmethod
    def from_files(cls, roles_file, user_assignment_file, permission_assignment_file):
        if os.path.isfile(roles_file):
            with open(roles_file.format(ROOT_DIR), 'rb') as input_file:
                roles, roles_count, user_names, permission_names = pickle.load(input_file)
        else:
            raise FileNotFoundError("Could not find the roles data file.")

        if os.path.isfile(user_assignment_file):
            user_assignment = pandas.read_csv(user_assignment_file, sep=';', index_col=0)
        else:
            raise FileNotFoundError("Could not find the user assignment file.")

        if os.path.isfile(permission_assignment_file):
            permission_assignment = pandas.read_csv(permission_assignment_file, sep=';', index_col=0)
        else:
            raise FileNotFoundError("Could not find the permission assignment file.")
        return cls(roles, roles_count, user_names, permission_names, user_assignment, permission_assignment)

    def persist(self):
        roles = (self.roles, self.roles_count, self.user_names, self.permission_names)
        with open('{}/user_data/role_data.pkl'.format(ROOT_DIR), 'wb') as output:
            pickle.dump(roles, output, -1)
        with open('{}/user_data/roles.json'.format(ROOT_DIR), 'w') as output:
            output.write(json.dumps(self.remap_keys(self.roles)))
        with open('{}/user_data/roles_count.json'.format(ROOT_DIR), 'w') as output:
            output.write(json.dumps(self.roles_count))
        self.user_assignment.to_csv(path_or_buf='{}/user_data/user_assignment.csv'.format(ROOT_DIR), sep=';')
        self.permission_assignment.to_csv(path_or_buf='{}/user_data/permission_assignment.csv'.format(ROOT_DIR),
                                          sep=';')

    def remap_keys(self, mapping):
        return [{'key': k, 'value': v} for k, v in mapping.items()]
