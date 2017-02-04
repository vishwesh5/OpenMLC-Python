import MLC.Log.log as lg
from MLC.mlc_parameters.mlc_parameters import Config
from MLC.Common.Operations import Operations
from MLC.Common.LispTreeExpr.TreeNodes import LeafNode, InternalNode
from MLC.Common.LispTreeExpr.OperationNodes import OpNodeFactory


class LispTreeExpr(object):

    def __init__(self, expr):
        self._nodes = []

        self._expanded_tree = expr

        # Remove the root part of the node
        nonroot_expr = expr[expr.find('root') + 5:-1]
        # lg.logger_.debug("[LISP_TREE_EXPR] NonRoot Expression: " + nonroot_expr)
        self._root, _ = self._generate_node(expr, is_root_expression=True)

        # Get the complexity of the tree before simplifying
        self._complexity = self._root.complexity()
        self._formal = self._root.formal()

        # Now, simplify the tree
        if Config.get_instance().getboolean('OPTIMIZATION', 'simplify'):
            self.simplify_tree()

    def simplify_tree(self):
        self._root = self._root.simplify()
        self._simplified_tree = '(root ' + self._root.to_string() + ')'
        lg.logger_.debug("[LISP_TREE_EXPR] Simplified Expression: " + self._simplified_tree)

    def calculate_expression(self, sensor_replacement_list):
        class Replace_Sensors_Visitor(TreeVisitor):

            def __init__(self, sensor_replacement_list):
                self._sensor_list = sensor_replacement_list

            def visit_internal_node(self, node):
                pass

            def visit_leaf_node(self, node):
                # FIXME: Don't like it. They should be private arguments
                if node.is_sensor():
                    # Get the number of the sensor
                    node._value = self._sensor_list[int(node._arg[1:])]
                else:
                    node._value = float(node._arg)

        # First, replace the sensors
        visitor = Replace_Sensors_Visitor(sensor_replacement_list)
        self._root.accept(visitor)
        return self._root.compute()

    def get_root_node(self):
        return self._root

    def get_expanded_tree_as_string(self):
        return '(root ' + self._root.to_string() + ')'

    def __str__(self):
        return self.get_expanded_tree_as_string()

    def get_simplified_tree_as_string(self):
        return self._simplified_tree

    def complexity(self):
        """
        The complexity of the tree is a number given by the weight of every operation and
        the amount of constants/sensors stored
        """
        return self._complexity

    def formal(self):
        """
        Return the tree as a MATLAB expression, in order to calculate the value of the individual
        """
        return self._formal

    def _number_of_subexpressions(self, expr):
        level = 0
        nbarg = 1
        for i in range(len(expr)):
            if expr[i] == '(':
                level += 1
            if expr[i] == ')':
                level -= 1
            if expr[i] == ' ' and level == 0:
                nbarg += 1
        return nbarg

    def _get_operation(self, expr, is_root_expression=False):

        if is_root_expression:
            root_prefix_len = len("(root ")
            return {"op": "root",
                    "nbarg": self._number_of_subexpressions(expr[root_prefix_len:len(expr) - 1]),
                    "complexity": 0}
        pos = -1
        expr_op = None
        # Get operation string
        str_op = expr[1:expr.find(' ')]

        # If the operation doesn not exists, an exception is thrown. This
        # shouldn't happen if the expression is valid
        try:
            expr_op = Operations.get_instance().get_operation_from_op_string(str_op)
        except KeyError:
            lg.logger_.error('[LISP_TREE_EXPR] Invalid operation found. Op: ', str_op)
            raise

        return expr_op

    def _generate_leaf_node(self, expr, parent_depth, expr_index):
        # We found a Leaf Node
        param_len = 0

        find_space = expr.find(' ')
        find_close_parenthesis = expr.find(')')

        # Find the first space or colon
        if find_space != -1 and find_space < find_close_parenthesis:
            param_len = find_space
        elif find_close_parenthesis != -1:
            param_len = find_close_parenthesis
        else:
            param_len = len(expr)

        leaf = LeafNode(expr[:param_len])
        leaf.set_depth(parent_depth)
        leaf.set_expr_index(expr_index)
        leaf.set_subtreedepth(0)
        self._nodes.append(leaf)
        return leaf, param_len + 1

    # As a precondition, the expression must be well-formed
    def _generate_node(self, expr, is_root_expression=False, parent_depth=0, expr_index=0):
        if expr[0] != '(':
            return self._generate_leaf_node(expr, parent_depth, expr_index)

        # We are in the presence of an internal node. Get the operation
        op = self._get_operation(expr, is_root_expression)

        # Generate the arguments of the internal node as Child Nodes
        node = OpNodeFactory.make(op["op"])
        node.set_depth(parent_depth + 1)
        node.set_expr_index(expr_index)
        expr_offset = 0
        offset = 0
        child_node = None
        child_subtreedepth = 0

        for i in range(op["nbarg"]):
            # 1 colon + op len + 1 space + (expr_offset)
            next_arg_pos = 1 + len(op["op"]) + 1 + expr_offset

            if expr[next_arg_pos] == '(':
                child_node, offset = self._generate_node(
                    expr[next_arg_pos:], parent_depth=parent_depth + 1, expr_index=expr_index + next_arg_pos)
            else:
                child_node, offset = self._generate_leaf_node(
                    expr[next_arg_pos:], parent_depth=parent_depth + 1, expr_index=expr_index + next_arg_pos)

            node.add_child(child_node)
            child_subtreedepth = max(child_subtreedepth, child_node.get_subtreedepth())
            expr_offset += offset

        node.set_subtreedepth(1 + child_subtreedepth)
        if not is_root_expression:
            self._nodes.append(node)
        next_arg_pos = 1 + len(op["op"]) + 1 + expr_offset + 1
        return node, next_arg_pos

    def leaf_nodes(self):
        for leaf in filter(lambda n: n.is_leaf(), self._nodes):
            yield leaf

    def internal_nodes(self):
        for leaf in filter(lambda n: not n.is_leaf(), self._nodes):
            yield leaf

    def nodes(self):
        for node in self._nodes:
            yield node


class TreeVisitor:

    def visit_internal_node(self, node):
        pass

    def visit_leaf_node(self, ndoe):
        pass