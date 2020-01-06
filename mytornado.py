import tornado.ioloop
import tornado.web
import tornado.websocket

class MainHandler(tornado.websocket.WebSocketHandler):
    waiters = []
    check = 123
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

class OwnerHandler(tornado.websocket.WebSocketHandler):
    datasets = {}
    n = 0

    def open(self):
        #verify that the data owner has connected with a valid token
        cookie = self.request.headers["cookie"]
        id = int(self.request.headers["id"])
        if cookie is not None:
            print("firebase call to verify that the cookie is valid:" + cookie)
            OwnerHandler.datasets[id] = self
            OwnerHandler.n += 1
            print("firebase call to update the list of available servers")

    def on_close(self):
        print("an owner has disconnected, need to let firebase know")
        OwnerHandler.datasets = {key: val for key, val in OwnerHandler.items() if val != self}

    def on_message(self, msg):
        print("looking at which researcher is currently connected to this owner and forwarding them the message")
        if len(ResearcherHandler.resMap[self]) > 0:
            ResearcherHandler.resMap[self][0].write_message(msg)

class ResearcherHandler(tornado.websocket.WebSocketHandler):
    dest = 0
    resMap = {}
    def open(self):
        #verify that the researcher has connected with a valid token
        cookie = self.request.headers["cookie"]
        if cookie is not None:
            print("firebase call to verify that the researcher cookie is valid:" + cookie) #also removes the token and returns the database id
            self.dest = int(self.request.headers["id"])
            if dest not in ResearcherHandler.resMap.keys():
                ResearcherHandler.resMap[OwnerHandler.datasets[self.dest]] = [self]
            else:
                ResearcherHandler.resMap[OwnerHandler.datasets[self.dest]].append(self)

    def on_close(self):
        ResearcherHandler.resMap[OwnerHandler.datasets[self.dest]].remove(self)

    def on_message(self, msg):
        #only send the message if they are first in line, otherwise, wait
        while(ResarcherHandler.resMap[OwnerHandler.datasets[self.dest]][0] is not self):
            sleep(1)
        OwnerHandler.datasets[self.dest].write_message(msg)

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/share", OwnerHandler),
        (r"/research", ResearcherHandler)
    ])
def check_origin(self, data):
    return True
if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
