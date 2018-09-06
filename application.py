import tornado.web

from ApplicationContext import ApplicationContext
from handlers import IndexHandler, InitHandler, ResetHandler, StatusHandler, VisualiseHandler, RoleSubmitHandler, \
    RoleHandler

from tornado.web import url

from definitions import ROOT_DIR


def app():
    application = tornado.web.Application([
        (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': "{}/static/".format(ROOT_DIR)}),

        url(r"/", IndexHandler.IndexHandler, name='index'),
        url(r"/reset", ResetHandler.ResetHandler, name='reset'),
        url(r"/init", InitHandler.InitHandler, name='init'),
        url(r"/init_algo", InitHandler.TriggerAlgoHandler, name='init_algo'),
        url(r"/init_overlay", InitHandler.OverlayHandler, name='init_overlay'),
        url(r"/init_meta_user", InitHandler.MetaUserHandler, name='init_meta_user'),
        url(r"/init_meta_permission", InitHandler.MetaPermHandler, name='init_meta_permission'),
        url(r"/reinit", InitHandler.ReInitHandler, name='reinit'),
        url(r"/readviser", InitHandler.ReAdviserHandler, name='readviser'),
        url(r"/status", StatusHandler.StatusHandler, name='status'),
        url(r"/status/api", StatusHandler.StatusHandlerApi, name='status_api'),
        url(r"/visualise/([123])", VisualiseHandler.VisualiseHandler, name='visualise'),
        url(r"/visualise/data/([123])", VisualiseHandler.VisualiseDataHandler, name='visualise_api'),
        url(r"/visualise/overlay", VisualiseHandler.VisualiseOverlayHandler, name='visualise_overlay'),
        url(r"/visualise/meta", VisualiseHandler.VisualiseMetaHandler, name='visualise_meta'),
        url(r"/visualise/export/([123])", VisualiseHandler.ExportVisualisationHandler, name='visualise_export'),
        url(r"/visualise/roles", VisualiseHandler.VisualiseRoleHandler, name='visualise_api_roles'),
        url(r"/submit_role", RoleSubmitHandler.RoleSubmitHandler),
        url(r"/apply_selection", RoleSubmitHandler.ApplySelectionHandler),
        url(r"/roles", RoleHandler.RoleHandler, name='roles'),
        url(r"/roles/delete/(.*)", RoleHandler.RoleDeleteHandler, name='delete_role'),
        url(r"/roles/render/(.*)", RoleHandler.RoleRenderHandler, name='render_role')
    ])
    application_context = ApplicationContext()
    application.context = application_context

    return application
