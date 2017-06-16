%%用来测试xxx_rbfnn文件。
%   测试我的RBF神经网络
Files = dir(fullfile('E:/stock_data/stocks_for_bpnn','*.csv'));
 LengthFiles = length(Files);
 mean_err = zeros(1,LengthFiles);
 mean_acc = zeros(1,LengthFiles);
 for i = 1:LengthFiles
     [err, acc] = xxx_rbfnn(strcat('E:/stock_data/stocks_for_bpnn/',Files(i).name));
     mean_err(i) = err;
     mean_acc(i) = acc;
 end
 
%  [err, acc] = xxx_rbfnn(strcat('E:/stock_data/stocks_for_bpnn/',Files(351).name));
%  disp(Files(350).name);