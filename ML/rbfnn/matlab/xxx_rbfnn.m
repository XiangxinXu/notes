function [ error, predict_accuracy] = xxx_rbfnn( filename )
%使用RBF神经网络计算股票预测涨跌幅
%   输入csv文件名，以前75%数据为训练数据，
%   后25%数据为测试数据。预测测试数据的股票当日涨跌幅。
%   返回平均误差（%）及预测涨跌的正确率。
M = readtable(filename);

M = table2cell(M);
p_change = cell2mat(M(:, 11));
yesterday_pchange = cell2mat(M(:, 16));
yesterday_close = cell2mat(M(:, 17));

[pchange_n, pchange_ps] = mapminmax(p_change');
[yes_pchange_n, yes_pchange_ps] = mapminmax(yesterday_pchange');
[yes_close_n, yes_close_ps] = mapminmax(yesterday_close');

train_length = size(p_change);
train_length = int16(train_length(1) *  0.75);
test_length = size(p_change);
test_length = test_length(1)-train_length;

in_train = [yes_pchange_n(:, 1:train_length); yes_close_n(:, 1:train_length)];
out_train = pchange_n(:, 1:train_length);

in_test = [yes_pchange_n( :, train_length + 1:end); yes_close_n(:, train_length + 1:end)];
out_test_r = pchange_n(:, train_length + 1:end);

rbfnn = newrb(in_train, out_train, 0.01, 0.2, 5);

out_test_d = rbfnn(in_test);

out_test_r = mapminmax('reverse', out_test_r, pchange_ps);
out_test_d = mapminmax('reverse', out_test_d, pchange_ps);

error = sum(abs(out_test_r - out_test_d))/double(test_length);
predict_accuracy = sign(out_test_d .* out_test_r);
predict_accuracy = sum(predict_accuracy == 1)/ double(test_length);

end

