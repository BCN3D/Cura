from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class BlockSlicingDecorator(SceneNodeDecorator):
    def __init__(self):
        super().__init__()

    def isBlockSlicing(self):
        return True

    def __deepcopy__(self, memo):
        return BlockSlicingDecorator()
