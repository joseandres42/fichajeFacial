class Known_people():
    def __init__(self):
        self.id = []
        self.name = []
        self.face_encoding = []
        self.picture = []

    def add(self,id,name,face_encoding, picture):
        self.id.append(id)
        self.name.append(name)
        self.face_encoding.append(face_encoding)
        self.picture.append(picture)

    def get_name_byid(self, id):
        return self.name[self.id.index(id)]

class Detected_people():
    def __init__(self):
        self.id = []
        self.location = []
        self.precision = []
        self.confirmed = []
        self.logged = []
        self.diff_location = []
        self.direction = []
        self.inframe = []

    def add(self,id,location):
        self.id.append(id)
        self.location.append(location)
        self.precision.append(5)
        self.diff_location.append(0)
        self.confirmed.append(False)
        self.logged.append(False)
        self.direction.append("unknown")
        self.inframe.append(True)

    def update(self,id,location,average_recog,out_of_scope):
        index =self.id.index(id)
        self.inframe[index]=True
        if self.precision[index] < out_of_scope:
            self.precision[index] +=2

        if self.confirmed[index] == False:
            if self.precision[index] > average_recog+5:
                self.confirmed[index] = True
                self.precision[index]=out_of_scope
                if self.diff_location[index] > 0:
                    self.direction[index] = "IN"
                else:
                    self.direction[index] = "OUT"

            if location[3] > self.location[index][3]:
                self.diff_location[index] += abs(location[3] - self.diff_location[index])
            else:
                self.diff_location[index] -= abs(location[3] - self.diff_location[index])

        self.location[index] =location

    def decr_prec(self):
        remove =[]
        for prec in self.precision:
            if prec == 0: remove.append(self.precision.index(prec))
            else:
                self.inframe[self.precision.index(prec)] =False
                self.precision[self.precision.index(prec)] -=1

        return remove

    def get(self, i):
        return self.id[i], self.location[i], self.precision[i]

    def get_index_byid(self, id):
        return self.id.index(id)

    def remove(self, i):
        self.id.pop(i)
        self.location.pop(i)
        self.precision.pop(i)
        self.confirmed.pop(i)
        self.logged.pop(i)
        self.diff_location.pop(i)
        self.direction.pop(i)
        self.inframe.pop(i)

