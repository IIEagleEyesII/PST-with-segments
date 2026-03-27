
class Point2D:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.segment = None


    def greaterX(self, other):
        return self.x> other.x or (self.x == other.x and self.y > other.y)
    def lesserX(self, other):
        return not other.greaterX(self)
    def greaterY(self, other):
        return self.y> other.y or (self.y == other.y and self.x > other.x)
    def lesserY(self, other):
        return not other.greaterY(self)
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class Segment:
    def __init__(self, p1, p2):
        """
        :attribute type: "vertical" or "horizontal"
        depending on the orientation of the segment, it will either have a left_point and a right_point or a upper_point and a lower_point
        """
        self.build(p1, p2)
        self.reported = 0

    def __repr__(self):
        if self.type == "vertical":
            return f"Segment({self.upper_point.x},{self.upper_point.y},{self.lower_point.x},{self.lower_point.y})"
        return f"Segment({self.left_point.x},{self.left_point.y},{self.right_point.x},{self.right_point.y})"

    def build(self, p1, p2):
        """
        Builds a segment from two points and assigns a type to it
        :param p1: first end
        :param p2: second end
        :return: None
        """
        if p1.x != p2.x and p1.y != p2.y:
            raise ValueError("Segment must be horizontal or vertical")
        else :
            if p1.x == p2.x:
                self.type = "vertical"
                if p1.y > p2.y:
                    self.upper_point = p1
                    self.lower_point = p2
                else: # <
                    self.lower_point = p1
                    self.upper_point = p2
                self.x = p1.x
            elif p1.y == p2.y:
                self.type = "horizontal"
                if p1.x > p2.x:
                    self.right_point = p1
                    self.left_point = p2
                else: # <
                    self.left_point = p1
                    self.right_point = p2
                self.y = p1.y
            p1.segment = self
            p2.segment = self

    """
    def __eq__(self, other):
        if not isinstance(other, Segment):
            return NotImplemented
        if self.type != other.type:
            return False
        if self.type == "vertical":
            return self.upper_point == other.upper_point and self.lower_point == other.lower_point
        return self.left_point == other.left_point and self.right_point == other.right_point

    def before_left(self, other):
        #for leftPST means a segment is on the left of the other
        if self.type == "horizontal" and other.type == "horizontal":
            return self.left_point.lesserX(other.left_point)
        else :
            raise ValueError("Segments must be both horizontal")

    def before_right(self, other):
        #for rightPST means a segment is on the right of the other
        if self.type == "horizontal" and other.type == "horizontal":
            return self.right_point.lesserX(other.left_point)
        else:
            raise ValueError("Segments must be both horizontal")"""


class PSTleft:
    """
     A leftPST is a custom primary search tree built to report segments in a window of type ]-INF,qx][qy,qy'] efficiently
        It is built on a list of horizontal segments sorted by their left endpoint's x coordinate.
         Each node of the tree contains a segment, a median y value, and two subtrees.
         The median y value is used to split the segments into two groups:
            -> segments with a left endpoint's y coordinate less than or equal to the median go to the left subtree
            ->segments with a left endpoint's y coordinate greater than the median go to the right subtree.
        The tree is built recursively until there are no more segments to split.
    Similarly a Right PST will be built to report segments in a window of type [qx,+INF)[qy,qy'] efficiently.
    When combined, we will hopefully be able to report segments in a window of type [qx,qy][qy',qy'] efficiently.
    Note : that these types of PSTs only work for horizontal segments and two other PSTs will be built to handle vertical segments.
    """

    def __init__(self, sortedSegments, is_sorted=False, renderer = None):
        if not is_sorted:
            sortedSegments = sorted(sortedSegments, key=lambda s: s.left_point.y)
        self.renderer = renderer # A pretty printer to report segments, it should have a method report(segment) that will be called for each segment in the query result
        self.medianY = None # The median y value of the segments in the subtree
        self.segment = None # The segment at the root of the subtree
        self.right_subtree = None # The right subtree of the tree
        self.left_subtree = None # The left subtree of the tree
        self.build(sortedSegments)

    def build(self, sortedSegments):
        """"
        Recursively builds a leftPST from a list of horizontal segments sorted by their left endpoint's x coordinate.
        Total build time is O(n log n), provided the pst is not imbalanced.
        """
        if not sortedSegments:
            return
        self.segment = min(sortedSegments, key=lambda s: s.left_point.x) # O(n)
        sortedSegmentsCopy = sortedSegments.copy()
        sortedSegmentsCopy.remove(self.segment)
        self.medianY, left_subtree_segments, right_subtree_segments = self.findMedianY(sortedSegmentsCopy)
        self.left_subtree = PSTleft(left_subtree_segments, is_sorted=True, renderer=self.renderer)
        self.right_subtree = PSTleft(right_subtree_segments, is_sorted=True, renderer=self.renderer)

    def findMedianY(self, segments_by_y):
        """
        Finds the median y value of a list of segments and splits the list into two sublists based on this median.
         The median is chosen as the y coordinate of the left endpoint of the segment at the middle of the list, and all segments with a left endpoint's y coordinate less than or equal to the median go to the left subtree, while all segments with a left endpoint's y coordinate greater than the median go to the right subtree.
         This function is used to build the leftPST and ensures that the tree is balanced, which is crucial for achieving efficient query times.
         The function runs in O(n) time, as it requires a single pass through the list of segments to find the median and split it into two sublists.
         Note that the input list of segments must be sorted by their left endpoint's y coordinate for this function to work correctly. (which is done initially before the built)
        :param segments_by_y: sorted list of segments
        :return: the median
        """

        def y_key(segment):
            """Helper function to extract the y coordinate of a segment."""
            if hasattr(segment, "left_point") and hasattr(segment.left_point, "y"):
                return segment.left_point.y
            if hasattr(segment, "y"):
                return segment.y
            raise ValueError("'coordinateless' segment found")

        #segments_by_y = sorted(sortedSegments, key=y_key)

        if not segments_by_y:
            return None, [], []

        n = len(segments_by_y)
        medianY = y_key(segments_by_y[(n - 1) // 2])  # médiane basse, elle sera toujours dans le sous-arbre gauche

        #slow but insures a correct split
        idx = (n - 1) // 2
        while idx < n and y_key(segments_by_y[idx]) == medianY:
            idx += 1

        left_subtree = segments_by_y[:idx]
        right_subtree = segments_by_y[idx:]

        for s in left_subtree:
            assert y_key(s) <= medianY, f"Segment {s} with y={y_key(s)} should be in the left subtree (medianY={medianY})"
        for s in right_subtree:
            assert y_key(s) > medianY, f"Segment {s} with y={y_key(s)} should be in the right subtree (medianY={medianY})"

        return medianY, left_subtree, right_subtree

    def findSplitNode(self, ymin, ymax):
        """
        Finds the node in the leftPST that contains the segment with the left endpoint's y coordinate between ymin and ymax.
        """
        node = self
        while node is not None and node.segment is not None and node.medianY is not None:
            if ymax <= node.medianY:
                node = node.left_subtree
            elif ymin > node.medianY:
                node = node.right_subtree
            else:
                return node
        return node if node is not None and node.segment is not None else None

    def reportInSubtree(self, qx):
        """
            Reports all segments in the subtree rooted at the current node that have a left endpoint's x coordinate less than or equal to qx.
            This function is used during the query process to report segments that are in the query window.
            The function runs in O(k) time, where k is the number of segments reported, as it requires a single pass through the subtree to find and report the relevant segments.
            Note that this function assumes that the segments in the subtree are sorted by their left endpoint's x coordinate, which is guaranteed by the way the tree is built.
        :param qx: 1D point corresponding to the query line
        :return: None
        """
        if self.segment is None:
            return
        if self.segment.left_point.x <= qx:
            self.renderer.report(self.segment)
        if self.left_subtree is not None:
            self.left_subtree.reportInSubtree(qx)
        if self.right_subtree is not None:
            self.right_subtree.reportInSubtree(qx)


    def initialQuery(self,qx, ymin, ymax):
        """
        Initiates the query
        :param qx:
        :param ymin:
        :param ymax:
        :return:
        """
        if self.segment is None or ymin > ymax:
            return
        splitNode = self.findSplitNode(ymin, ymax)
        if splitNode is not None:
            splitNode.query(qx,ymin, ymax)

    def query(self, qx, ymin, ymax):
        """
        The actual query function that reports all segments in the subtree rooted Vsplit
        """
        if self.segment is None:
            return

        current_y = self.segment.left_point.y
        if self.segment.left_point.x <= qx and ymin <= current_y <= ymax:
            self.renderer.report(self.segment)

        if self.medianY is None:
            return

        left_path = self.left_subtree
        while left_path is not None and left_path.segment is not None:
            y = left_path.segment.left_point.y
            if left_path.segment.left_point.x <= qx and ymin <= y <= ymax:
                self.renderer.report(left_path.segment)

            if left_path.medianY is None:
                break
            if ymin <= left_path.medianY:
                if left_path.right_subtree is not None:
                    left_path.right_subtree.reportInSubtree(qx)
                left_path = left_path.left_subtree
            else:
                left_path = left_path.right_subtree

        right_path = self.right_subtree
        while right_path is not None and right_path.segment is not None:
            y = right_path.segment.left_point.y
            if right_path.segment.left_point.x <= qx and ymin <= y <= ymax:
                self.renderer.report(right_path.segment)

            if right_path.medianY is None:
                break
            if ymax > right_path.medianY:
                if right_path.left_subtree is not None:
                    right_path.left_subtree.reportInSubtree(qx)
                right_path = right_path.right_subtree
            else:
                right_path = right_path.left_subtree
