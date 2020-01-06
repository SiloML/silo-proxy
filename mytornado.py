import tornado.ioloop
import tornado.web
import tornado.websocket
class MainHandler(tornado.websocket.WebSocketHandler):
    waiters = []
    def open(self):
        MainHandler.waiters.append(self)
        print(self)
        print("added")
    def on_close(self):
        MainHandler.waiters.remove(self)
        print("do nothing")
    def on_message(self, msg):
        for waiter in MainHandler.waiters:
            waiter.write_message("someone said ", msg)
class AcceptOwnerHandler(tornado.websocket.WebSocketHandler):
    async def open(self):
        #define the url using some firebase call
        conn = await websocket_connect(url)
        print("hello")
        async def proxy_loop():
            while True:
                msg = await conn.read_message()
                if msg is None:
                    break
                print(msg)
                await self.write_message(msg)
        ioloop.IOLoop.current().spawn_callback(proxy_loop)
    async def on_close(self):
        return
    async def on_message(self, msg):
        print("forwarding message")
class AuthorizeUserHandler(tornado.websocket.WebSocketHandler):
    async def open(self):
        #define the url using some firebase call
        print("connected")
        #conn = await websocket_connect("http://54.183.80.47:10000")
        async def proxy_loop():
            while True:
                msg = await conn.read_message()
                if msg is None:
                    break
                print("msg:", msg)
                await self.write_message(msg)
        ioloop.IOLoop.current().spawn_callback(proxy_loop)
def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/AcceptOwner", AcceptOwnerHandler),
        (r"/AuthorizeUser", AuthorizeUserHandler)
    ])
def check_origin(self, data):
    return True
if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
