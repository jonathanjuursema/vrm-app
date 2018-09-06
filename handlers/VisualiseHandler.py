import tornado.web
import json
import io

from PIL import Image
from definitions import ROOT_DIR


class VisualiseHandler(tornado.web.RequestHandler):
    def get(self, matrix_number):
        self.render("visualise.html", matrix_number=matrix_number, context=self.application.context)


class VisualiseDataHandler(tornado.web.RequestHandler):
    def get(self, matrix_number):
        matrix_number = int(matrix_number)
        if matrix_number is 1 and self.application.context.stage >= 2:
            up = self.application.context.original_up.to_json(orient='split')
        elif matrix_number is 2 and self.application.context.stage >= 6:
            up = self.application.context.optimised_up.to_json(orient='split')
        elif matrix_number is 3 and self.application.context.stage >= 6:
            up = self.application.context.working_up.to_json(orient='split')
        else:
            up = "Unknown matrix number {} for stage {}.".format(matrix_number, self.application.context.stage)
        self.write(up)


class VisualiseOverlayHandler(tornado.web.RequestHandler):
    def get(self):
        up = self.application.context.overlay_up
        if up is not None:
            self.write(self.application.context.overlay_up.to_json(orient='split'))
        else:
            self.write("No overlay available.")


class VisualiseMetaHandler(tornado.web.RequestHandler):
    def get(self):
        meta = {'user': None, 'permission': None}
        if self.application.context.user_meta is not None:
            meta['user'] = json.loads(self.application.context.user_meta.to_json(orient='records'))
        if self.application.context.permission_meta is not None:
            meta['permission'] = json.loads(self.application.context.permission_meta.to_json(orient='records'))
        self.write(meta)


class VisualiseRoleHandler(tornado.web.RequestHandler):
    def get(self):
        self.write(json.dumps(self.application.context.generated_roles))


class ExportVisualisationHandler(tornado.web.RequestHandler):
    def get(self, matrix_number):
        matrix_number = int(matrix_number)
        if matrix_number is 1 and self.application.context.stage >= 2:
            up = self.application.context.original_up
        elif matrix_number is 2 and self.application.context.stage >= 6:
            up = self.application.context.optimised_up
        elif matrix_number is 3 and self.application.context.stage >= 6:
            up = self.application.context.working_up

        image = Image.new('RGBA', up.shape[::-1])

        pixels = image.load()

        up_matrix = up.as_matrix()

        overlay_matrix = self.application.context.overlay_up.as_matrix() if self.application.context.overlay_up is not None else None

        for user in range(0, up.shape[0]):
            for perm in range(0, up.shape[1]):
                color = (255, 255, 255)
                if up_matrix[user][perm]:
                    color = (0, 0, 0)
                if overlay_matrix is not None and overlay_matrix[user][perm] > 0:
                    color = (255, 255, 0) if up_matrix[user][perm] else (255, 0, 0)

                pixels[perm, user] = color

        image_bytes = io.BytesIO();
        image.save(image_bytes, 'PNG')

        self.set_header('Content-Type', 'image/png')
        self.set_header('Content-Disposition', 'attachment; filename=up_export.png')

        self.write(image_bytes.getvalue())
        self.finish()
