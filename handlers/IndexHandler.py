import tornado.web


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        if self.application.context.stage == 0:
            self.redirect(r'/init')
        elif self.application.context.stage == 1:
            self.render("../error.html", error_message="Data is currently being loaded. Try again in a few seconds.")
        elif self.application.context.stage >= 2:
            self.redirect(self.reverse_url('status'))
        else:
            self.render("../error.html", error_message="I'm not sure what to do. Stage: {}.".format(
                self.application.context.stage))
