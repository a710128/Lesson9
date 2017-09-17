import pickle
import threading
from room.room import Room
from API import User


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

    def __del__(self):
        """
        pickle.dump({
            'rooms': self.rooms,
            'ship': self.ship
        }, open('backup.pkl', 'wb'))
        """
        pass

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
