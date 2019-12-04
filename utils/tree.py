class Tree(object):

    def __init__(self, name, left=None, right=None):
        self.scope = None
        self.name = name
        self.left = left
        self.right = right

    def __str__(self):
        res = str(self.name)
        if self.left is not None:
            res += ";" + str(self.left)
        if self.right is not None:
            res += ";" + str(self.right)
        return res

    def __repr__(self):
        return str(self)

