from definitions import ROOT_DIR

from handlers.InitHandler import ExtractThread

import tornado.web
import tornado.escape

import json
import random
import string


class RoleSubmitHandler(tornado.web.RequestHandler):
    def post(self):
        t_role = tornado.escape.json_decode(self.request.body)
        role = {
            'id': ''.join(random.choices(string.ascii_uppercase + string.digits, k=20)),
            'render': True,
            'name': t_role['name'],
            'users': t_role['users'],
            'permissions': t_role['permissions'],
        }
        roles = self.application.context.generated_roles
        roles.append(role)
        self.application.context.generated_roles = roles
        with open('{}/user_data/generated_roles.json'.format(ROOT_DIR), 'w') as output:
            output.write(json.dumps(self.application.context.generated_roles))


class ApplySelectionHandler(tornado.web.RequestHandler):
    def post(self):
        t_data = tornado.escape.json_decode(self.request.body)
        for user in t_data['users']:
            for permission in t_data['permissions']:
                for up in [self.application.context.original_up,
                           self.application.context.working_up,
                           self.application.context.optimised_up]:
                    up.at[user, permission] = t_data['grant']

        self.application.context.original_up.to_csv(path_or_buf='{}/user_data/original_up.csv'.format(ROOT_DIR), sep=';')
