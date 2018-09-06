import tornado.web
import numpy


class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        if self.application.context.stage < 2:
            self.redirect(self.reverse_url('init'))
        else:
            self.render("status.html", context=self.application.context)


class StatusHandlerApi(tornado.web.RequestHandler):
    def get(self):
        self.write({'stage': self.application.context.stage, 'percentage': self.application.context.stage_percentage})
