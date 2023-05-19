# this code is not important to the AI project, it's only used in the wordle base game and environment
# this was written a year ago in another class.

class NoInput(Exception):
    pass


class NotFoundException(Exception):
    pass


class ItemExistsException(Exception):
    pass

class Node:
    def __init__(self, key=None, data=None, next=None):
        self.key = key
        self.data = data
        self.next = next

    def __len__(self):
        counter = 0
        while temp is not None:
            temp = self.next
            counter += 1
        return counter

class HashMap:
    # This is the exact hashmap I used in PA5
    # except I have fewer buckets and each one is bigger
    def __init__(self, capacity=2):
        self.capacity = capacity
        self.hash_table = [Bucket() for _ in range(self.capacity)]
        self.item_count = 0

    def check_count(self):
        if self.item_count >= self.capacity * 10:
            self.rebuild()

    def rebuild(self):
        nexthash = HashMap(self.capacity * 2)
        for eachbucket in self.hash_table:
            while eachbucket.head is not None:
                nexthash.insert(eachbucket.head.key, eachbucket.head.data)
                eachbucket.remove(eachbucket.head.key)
        self.capacity = nexthash.capacity
        self.hash_table = nexthash.hash_table
        self.item_count = nexthash.item_count

    def indexing(self, key):
        return hash(key) % self.capacity

    def __str__(self):
        hash_string = ""
        for _ in self.hash_table:
            hash_string += str(_) + "\n"
        return hash_string

    def __setitem__(self, key, data):
        if self.hash_table[self.indexing(key)].contains(key):
            self.hash_table[self.indexing(key)][key] = data
        else:
            self.hash_table[self.indexing(key)].insert(key, data)
            self.item_count += 1
            self.check_count()

    def __getitem__(self, key):
        return self.hash_table[self.indexing(key)].find(key)

    def __len__(self):
        return self.item_count

    def insert(self, key, data):
        self.hash_table[self.indexing(key)].insert(key, data)
        self.item_count += 1
        self.check_count()

    def update(self, key, data):
        self.hash_table[self.indexing(key)].update(key, data)

    def find(self, key):
        return self.hash_table[self.indexing(key)].find(key)

    def contains(self, key):
        return self.hash_table[self.indexing(key)].contains(key)

    def remove(self, key):
        self.hash_table[self.indexing(key)].remove(key)
        self.item_count -= 1


class Bucket:
    def __init__(self, node=None):
        self.head = node
        if node is None:
            self.size = 0
        else:
            self.size = len(node)

    def __str__(self, node=None):
        temp = self.head
        next_string = ""
        while temp is not None:
            next_string += "(K:" + str(temp.key) + ", D:" + str(temp.data) + ") --> "
            temp = temp.next
        return next_string + "None"

    def insert(self, key, data):
        if self.head is None:
            self.head = Node(key, data)
        else:
            if self.contains(key):
                raise ItemExistsException()
            temp = self.head
            self.head = Node(key, data)
            self.head.next = temp
        self.size += 1

    def update(self, key, data):
        self.find_rec(self.head, key, 0, [1, data])

    def __setitem__(self, key, data):
        try:
            self.find(key)
            self.update(key, data)
        except NotFoundException:
            self.insert(key, data)

    def __getitem__(self, key):
        return self.find(key)

    def __len__(self):
        return self.size

    def find(self, key):
        return self.find_rec(self.head, key)

    def find_rec(self, node, key, removal=0, update=[0, 0]):
        if node is None:
            raise NotFoundException
        elif node.key == key:
            if removal:
                self.head = node.next
                self.size -= 1
                return
            if update[0]:
                node.data = update[1]
            return node.data
        else:
            if removal and node.next is None:
                if node.key == key:
                    node = None
                    self.size -= 1
                else:
                    raise NotFoundException
            elif removal and node.next.key == key:
                node.next = node.next.next
                self.size -= 1
                return
            return self.find_rec(node.next, key, removal, update)

    def contains(self, key):
        try:
            self.find(key)
            return True
        except NotFoundException:
            return False

    def get_at_index(self, index, node=None, counter=0):
        if node is None:
            node = self.head
        if index == counter:
            return node.key
        else:
            return self.get_at_index(index, node.next, counter + 1)

    def remove(self, key):
        self.find_rec(self.head, key, 1)
