import tornado.web
import os
import threading
import pandas

from definitions import ROOT_DIR

from ApplicationContext import ApplicationContext, RoleData

from algorithms.ExtractAlgorithm import ExtractAlgorithm
from algorithms.AdviserAlgorithm import AdviserAlgorithm


class InitHandler(tornado.web.RequestHandler):
    def get(self):
        if self.application.context.stage != 0:
            self.render("../error.html", error_message="The application is already initiated. Stage: {}.".format(
                self.application.context.stage))
        else:
            self.render("init.html")

    def post(self):
        if self.application.context.stage != 0:
            self.render("../error.html", error_message="The application is already initiated. Stage: {}.".format(
                self.application.context.stage))

        elif 'source-file' not in self.request.files.keys():
            self.render("../error.html", error_message="No file was uploaded.")

        else:
            self.application.context.stage = 1
            file = self.request.files['source-file'][0]
            file_handler = open('{}/user_data/original_up.csv'.format(ROOT_DIR), 'wb')
            file_handler.write(file['body'])
            file_handler.close()
            read_status = self.application.context.load_original_data()
            if not read_status:
                self.application.context.stage = 0
                try:
                    os.remove('{}/user_data/original_up.csv'.format(ROOT_DIR))
                finally:
                    self.render("../error.html", error_message="The uploaded file was not in the correct format.")
            else:
                self.application.context.stage = 2
                self.redirect(self.reverse_url('index'))

                extract_thread = ExtractThread(self.application.context)
                self.application.context.stage = 3


class OverlayHandler(tornado.web.RequestHandler):
    def get(self):
        if self.application.context.stage is 0:
            self.render("../error.html", error_message="Please initialise the application first. Stage: {}.".format(
                self.application.context.stage))
        else:
            self.render("init_overlay.html")

    def post(self):
        if self.application.context.stage is 0:
            self.render("../error.html", error_message="Please initialise the application first. Stage: {}.".format(
                self.application.context.stage))

        elif 'source-file' not in self.request.files.keys():
            self.render("../error.html", error_message="No file was uploaded.")

        else:
            file = self.request.files['source-file'][0]
            file_handler = open('{}/user_data/overlay.csv'.format(ROOT_DIR), 'wb')
            file_handler.write(file['body'])
            file_handler.close()
            read_status = self.application.context.load_original_data()
            if not read_status:
                self.application.context.stage = 0
                try:
                    os.remove('{}/user_data/overlay.csv'.format(ROOT_DIR))
                finally:
                    self.render("../error.html", error_message="The uploaded file was not in the correct format.")
            else:
                self.redirect(self.reverse_url('index'))


class MetaUserHandler(tornado.web.RequestHandler):
    def get(self):
        if self.application.context.stage is 0:
            self.render("../error.html", error_message="Please initialise the application first. Stage: {}.".format(
                self.application.context.stage))
        else:
            self.render("init_meta_user.html")

    def post(self):
        if self.application.context.stage is 0:
            self.render("../error.html", error_message="Please initialise the application first. Stage: {}.".format(
                self.application.context.stage))

        elif 'source-file' not in self.request.files.keys():
            self.render("../error.html", error_message="No file was uploaded.")

        else:
            file = self.request.files['source-file'][0]
            file_handler = open('{}/user_data/meta_user.csv'.format(ROOT_DIR), 'wb')
            file_handler.write(file['body'])
            file_handler.close()
            read_status = self.application.context.load_original_data()
            if not read_status:
                self.application.context.stage = 0
                try:
                    os.remove('{}/user_data/meta_user.csv'.format(ROOT_DIR))
                finally:
                    self.render("../error.html", error_message="The uploaded file was not in the correct format.")
            else:
                self.redirect(self.reverse_url('index'))


class MetaPermHandler(tornado.web.RequestHandler):
    def get(self):
        if self.application.context.stage is 0:
            self.render("../error.html", error_message="Please initialise the application first. Stage: {}.".format(
                self.application.context.stage))
        else:
            self.render("init_meta_permission.html")

    def post(self):
        if self.application.context.stage is 0:
            self.render("../error.html", error_message="Please initialise the application first. Stage: {}.".format(
                self.application.context.stage))

        elif 'source-file' not in self.request.files.keys():
            self.render("../error.html", error_message="No file was uploaded.")

        else:
            file = self.request.files['source-file'][0]
            file_handler = open('{}/user_data/meta_permission.csv'.format(ROOT_DIR), 'wb')
            file_handler.write(file['body'])
            file_handler.close()
            read_status = self.application.context.load_original_data()
            if not read_status:
                self.application.context.stage = 0
                try:
                    os.remove('{}/user_data/meta_permission.csv'.format(ROOT_DIR))
                finally:
                    self.render("../error.html", error_message="The uploaded file was not in the correct format.")
            else:
                self.redirect(self.reverse_url('index'))


class TriggerAlgoHandler(tornado.web.RequestHandler):
    def get(self):
        self.application.context.stage = 2
        self.redirect(self.reverse_url('index'))

        extract_thread = ExtractThread(self.application.context)
        self.application.context.stage = 3


class ExtractThread:

    def __init__(self, application: ApplicationContext):
        self.application = application
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):

        # Generate working UP
        try:
            self.application.working_up = pandas.read_csv('{}/user_data/original_up.csv'.format(ROOT_DIR),
                                                          sep=';', index_col=0)
        finally:
            pass

        # Remove non-rendered roles.
        up = self.application.working_up
        for role in self.application.generated_roles:
            if role['render']:
                continue

            for user in role['users']:
                for permission in role['permissions']:
                    up.at[user, permission] = False

        up = up.loc[:, (up != 0).any(axis=0)]
        up = up.loc[(up != 0).any(axis=1), :]

        self.application.working_up = up

        extract = ExtractAlgorithm(self.application)
        extract.execute(1000)

        self.application.stage = 5

        self.application.role_data = RoleData(roles=extract.get_pseudo_roles(),
                                              roles_count=extract.get_pseudo_roles_count(),
                                              user_names=extract.get_user_names(),
                                              permission_names=extract.get_permission_names(),
                                              user_assignment=extract.get_pseudo_user_assignment(),
                                              permission_assignment=extract.get_pseudo_permission_assignment())

        self.application.role_data.persist()

        adviser_thread = AdviserThread(self.application)


class ReInitHandler(tornado.web.RequestHandler):
    def get(self):
        self.application.context.stage = 2
        self.redirect(self.reverse_url('index'))
        extract_thread = ExtractThread(self.application.context)
        self.application.context.stage = 3


class ReAdviserHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect(self.reverse_url('index'))
        adviser_thread = AdviserThread(self.application.context)
        self.application.context.stage = 5


class AdviserThread:

    def __init__(self, application: ApplicationContext):
        self.application = application
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        adviser = AdviserAlgorithm(self.application)
        adviser.execute()

        self.application.optimised_up = adviser.get_sorted_up(self.application.working_up)
        self.application.optimised_up.to_csv(path_or_buf='{}/user_data/optimised_up.csv'.format(ROOT_DIR), sep=';')

        if self.application.overlay_up is not None:
            self.application.overlay_up = adviser.get_sorted_overlay(self.application.overlay_up)
            self.application.overlay_up.to_csv(path_or_buf='{}/user_data/overlay.csv'.format(ROOT_DIR), sep=';')

        self.application.stage = 6
