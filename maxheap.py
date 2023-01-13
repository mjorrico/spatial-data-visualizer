import numpy as np


class Maxheap(object):
    def __init__(self):
        self.head = None

    def insert(self, node: "Node"):
        if self.head is None:
            self.head = node
        elif node.score_gain >= self.head.score_gain:
            node.child = self.head
            self.head = node
        else:
            heap_node = self.head
            while heap_node is not None:
                if (
                    heap_node.child is None
                    or node.score_gain >= heap_node.child.score_gain
                ):
                    node.child = heap_node.child
                    heap_node.child = node
                    break
                heap_node = heap_node.child

    def poptop(self):
        if self.head is not None:
            top_node = self.head.copy()
            self.head = self.head.child
            return top_node

    def __repr__(self):
        output = []
        heap_node = self.head
        while heap_node is not None:
            output.append(str(heap_node))
            heap_node = heap_node.child
        return "\n".join(output)


class Node:
    def __init__(self, obj_id, score_gain, iter) -> None:
        self.obj_id = obj_id
        self.score_gain = score_gain
        self.iter = iter
        self.child: Node = None

    def copy(self):
        return Node(self.obj_id, self.score_gain, self.iter)

    def __repr__(self):
        return f"{[self.obj_id, self.score_gain, self.iter]}"
