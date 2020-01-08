import tornado.ioloop
import tornado.web
import tornado.websocket
from tornado.queues import Queue
import requests

class OwnerHandler(tornado.websocket.WebSocketHandler):
    datasets = {}
    id = 0
    def open(self):
        #verify that the data owner has connected with a valid token
        cookie = self.request.headers["cookie"]
        if cookie is not None:
            token, dataset = cookie.split(",")
            self.id = int(dataset)
            print("firebase call to verify that the cookie is valid:" + cookie)
            val = requests.get("http://us-central1-silo-ml.cloudfunctions.net/verifyOwnerToken", params={'token': token, 'dataset': dataset})
            if (val.status_code == 200):
                self.id = val.content
                OwnerHandler.datasets[self.id] = (self, Queue(maxsize=1))
        else:
            return False

    def on_close(self):
        print("an owner has disconnected, need to let firebase know")
        requests.get("http://us-central1-silo-ml.cloudfunctions.net/disconnectDevice", params={'dataset_id': dataset})
        del OwnerHandler.datasets[self.id]


    def on_message(self, msg):
        print("looking at which researcher is currently connected to this owner and forwarding them the message")
        if OwnerHandler.datasets[self.id][1].qsize() > 0:
            ResearcherHandler.resMap[self].write_message(msg)

class ResearcherHandler(tornado.websocket.WebSocketHandler):
    dest = 0
    resMap = {}
    async def open(self):
        #verify that the researcher has connected with a valid token
        cookie = self.request.headers["cookie"]
        if cookie is not None:
            print("firebase call to verify that the researcher cookie is valid:" + cookie) #also removes the token and returns the database id
            token, dataset = cookie.split(",")
            val = requests.get("http://us-central1-silo-ml.cloudfunctions.net/verifyResearcherToken", params={'token': token, 'dataset': dataset})
            if (val.status_code == 200):
                self.dest = dataset
                print(self)
                await OwnerHandler.datasets[self.dest][1].put(self)
                ResearcherHandler.resMap[OwnerHandler.datasets[self.dest][0]] = self
        else:
            return False

    def on_close(self):
        print("researcher closing")
        if (ResearcherHandler.resMap[OwnerHandler.datasets[self.dest][0]] == self):
            print("removing")
            OwnerHandler.datasets[self.dest][1].task_done()
            print(OwnerHandler.datasets[self.dest][1].get_nowait())

    def on_message(self, msg):
        #only send the message if they are first in line
        OwnerHandler.datasets[self.dest][0].write_message(msg)

def make_app():
    return tornado.web.Application([
        (r"/", OwnerHandler),
        (r"/share", OwnerHandler),
        (r"/research", ResearcherHandler)
    ])

def check_origin(self, data):
    return True
if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
