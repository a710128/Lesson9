import pickle
import threading
from room.room import Room
from API import User, UserException


class Manager:
    def __init__(self, rooms=None, ship=None):
        if rooms is None:
            rooms = []
        if ship is None:
            ship = {}

        assert isinstance(rooms, list) and isinstance(ship, dict), "Parameter type error"
        self.rooms = rooms  # Room
        self.ship = ship    # User -> Room
        self.__lock = threading.Lock()

    def dump(self):
        pickle.dump({
            'rooms': self.rooms,
            'ship': self.ship
        }, open('backup.pkl', 'wb'))

    def getUser(self, uid: str) -> User:
        assert isinstance(uid, str), "Parameter type error"
        ret = None
        self.__lock.acquire()
        for u in self.ship.keys():
            if u.name == uid:
                ret = u
                break
        self.__lock.release()
        return ret

    def addUser(self, uid: str, passwd: str) -> User:
        assert isinstance(uid, str) and isinstance(passwd, str), "Parameter type error"
        if self.getUser(uid) is not None:
            return None
        try:
            user = User(uid, passwd)
        except UserException as e:
            return None
        self.__lock.acquire()
        self.ship[user] = None
        self.__lock.release()
        return user

    def delUser(self, uid):
        user = self.getUser(uid)
        if user is None:
            return
        self.__lock.acquire()
        if self.ship[user] is not None:
            self.ship[user].delUser(user)
            self.ship[user] = None
        del self.ship[user]
        del user
        self.__lock.release()

    def exitRoom(self, uid):
        user = self.getUser(uid)
        if user is None:
            return
        self.__lock.acquire()
        if self.ship[user] is not None:
            self.ship[user].delUser(user)
            self.ship[user] = None
        self.__lock.release()

    def joinRoom(self, room, user: User):
        assert isinstance(room, (Room, int)) and isinstance(user, User), "Parameter type error"
        self.__lock.acquire()

        if not (self.ship[user] is None):
            self.ship[user].delUser(user)
            self.ship[user] = None

        if isinstance(room, int):
            it = 0
            while it < len(self.rooms):
                if self.rooms[it].roomId == room:
                    break
                it += 1
            if it < len(self.rooms):
                self.rooms[it].addUser(user)
                self.ship[user] = self.rooms[it]
        else:
            if room in self.rooms:
                room.addUser(user)
            else:
                self.rooms.append(room)
                room.addUser(user)
                threading.Thread(target=self._roomHandler, args=(room, )).start()
            self.ship[user] = room

        self.__lock.release()

    def _roomHandler(self, room: Room):
        room.loop()  # start room loop
        # del room
        self.__lock.acquire()
        it = 0
        while it < len(self.rooms):
            if self.rooms[it] == room:
                break
            it += 1
        assert it < len(self.rooms), "Unknown error when room handler"
        for u in room.user:
            self.ship[u] = None
        del self.rooms[it]
        self.__lock.release()

    def run(self):
        thds = [threading.Thread(target=self._roomHandler, args=(r, )) for r in self.rooms]
        for t in thds:
            t.start()
