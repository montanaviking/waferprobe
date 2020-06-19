# Phil Marsh Carbonics Inc
# try out Python tree
# reference: http://stackoverflow.com/questions/2482602/a-general-tree-implementation-in-python







class Node(object):
    def __init__(self, data):
        self.data = data
        self.levelname
        self.children = []

    def add_child(self, obj):
        self.children.append(obj)