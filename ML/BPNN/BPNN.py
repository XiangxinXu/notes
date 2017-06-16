# coding=utf-8
###
#  @author xxx
#  created on 2016.6.29
###
import numpy as np
from math import *


class BPNN:

    def __init__(self, X, Y):
        self.X = X
        self.Y = Y
        self.eta1 = 0.0002
        self.eta2 = 0.0002
        print X.shape
        self.test_count = X.shape[0]
        self.feature_count = X.shape[-1]
        self.output_count = Y.shape[1]

        # it is said that sqrt(output node number + input node number) + 5 is a feasible h_node_number.
        self.h_node_number = ceil(sqrt(self.output_count + self.feature_count) + 5)
        np.random.seed(0)
        self.W1 = 2 * np.random.rand(int(self.feature_count), int(self.h_node_number)) - 1
        self.W2 = 2 * np.random.rand(int(self.h_node_number), int(self.output_count)) - 1
        print "test case size: {0}, X node number: {1}, \
        hidden layer node number: {2}, Y node number: {3}"\
            .format(self.test_count, self.feature_count, self.h_node_number, self.output_count)
        self.normalize()

    def normalize(self):
        self.X = np.apply_along_axis(lambda a: (a - a.min()) / float(a.max() - a.min()), axis=0, arr=self.X)
        self.Y = np.apply_along_axis(lambda a: (a - a.min()) / float(a.max() - a.min()), axis=0, arr=self.Y)

        print self.X
        print self.Y

    def activate_func(self, x, derivative=0):
        if derivative == 0:
            # use np.exp instaad of math.exp to enable array-like data computing
            return 1.0 / (1 + np.exp(-x))
        else:
            return self.activate_func(x) * (1 - self.activate_func(x))

    def train(self, train_time=100, precision=0.001):

        for i in range(train_time):
            test_case_id = i % self.Y.shape[0]

            input_x_shape = tuple([1] + list(self.X[test_case_id].shape))
            input_y_shape = tuple([1] + list(self.Y[test_case_id].shape))
            input_x = self.X[test_case_id].reshape(input_x_shape)
            input_y = self.Y[test_case_id].reshape(input_y_shape)

            #get value of hidden node
            net1 = np.dot(input_x, self.W1)
            #output value of hidden node after activated(normalized)
            hidden_node = self.activate_func(net1)

            #get value of output node
            net2 = np.dot(hidden_node, self.W2)
            #output value of output node after activated(normalized)
            trained_y = self.activate_func(net2)

            error_y = trained_y - input_y
            #if i%700==0:
            #    print('test_case:%d'%test_case_id)
            #    print(self.X[test_case_id])
            #    print(self.Y[test_case_id])

            delta_w2 = error_y * self.activate_func(net2, 1)
            adjust_w2 = - self.eta2 * np.dot(hidden_node.T, delta_w2)

            delta_w1 = np.dot(self.W2, delta_w2.T) * self.activate_func(net1, 1).T
            adjust_w1 = -self.eta1 * np.dot(delta_w1, input_x).T

            self.W1 += adjust_w1
            self.W2 += adjust_w2

    def predict(self, x):
        res = None
        for case in x:
            net1 = case.dot(self.W1)
            hidden_layer = self.activate_func(net1)

            net2 = hidden_layer.dot(self.W2)
            y = self.activate_func(net2)

            if res is not None:
                res = np.vstack((res, [y]))
            else:
                res = np.asarray([y])

        return res


if __name__ == '__main__':

    X = np.array([[2, 2, 2, 2, 2],
            [0, 3, 6, 1, 7],
            [1, 2, 1, 9, 4],
            [1, 1, 1, 1, 1],
            [4, 5, 7, 2, 7],
            [4, 4, 4, 4, 4],
            [2, 2, 2, 2, 2],
            [3, 2, 7, 3, 6],
            [3, 3, 2, 6, 1]])

    XX = np.array([[0, 0],
                  [0, 1],
                  [1, 1],
                  [ 1, 0]])

    Y = np.array([[0, 1],
                 [1, 2],
                 [1, 1],
                 [0, 3],
                 [1, 4],
                 [0, 4],
                 [0, 2],
                 [1, 0],
                 [1, 2]])

    YY = np.array([[0],
                  [1],
                  [0],
                  [1]])

    bpnn = BPNN(X, Y)

    bpnn.train(100000)

    print(X)
    print(Y)

    print bpnn.predict(X)
