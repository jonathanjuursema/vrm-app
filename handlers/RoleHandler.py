from definitions import ROOT_DIR

import tornado.web
import tornado.escape

import json


class RoleHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('roles.html', roles=self.application.context.generated_roles)


class RoleDeleteHandler(tornado.web.RequestHandler):
    def get(self, role_id):
        roles = self.application.context.generated_roles
        roles[:] = [r for r in roles if r['id'] != role_id]
        save_roles(self)
        self.redirect(self.reverse_url('roles'))


class RoleRenderHandler(tornado.web.RequestHandler):
    def get(self, role_id):
        roles = self.application.context.generated_roles
        for role in roles:
            if role['id'] == role_id:
                role['render'] = not role['render']
                save_roles(self)
                self.redirect(self.reverse_url('roles'))


def save_roles(app):
    with open('{}/user_data/generated_roles.json'.format(ROOT_DIR), 'w') as output:
        output.write(json.dumps(app.application.context.generated_roles))
