import tornado.web
from application import app


if __name__ == "__main__":
    print("Building app...")
    app = app()
    print("Listening...")
    app.listen(8080)
    print("Starting loop...")
    tornado.ioloop.IOLoop.current().start()