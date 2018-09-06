import tornado.web
import os
from definitions import ROOT_DIR


class ResetHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("reset.html")

    def post(self):
        self.application.context.stage = 0
        self.application.context.generated_roles = []

        folder = '{}/user_data/'.format(ROOT_DIR)
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            finally:
                pass

        self.redirect(self.reverse_url('index'))
