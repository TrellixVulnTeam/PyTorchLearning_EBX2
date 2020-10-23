# -*- coding: utf-8 -*-#

import os
import sys
import time

from sklearn.model_selection import KFold
from torch.utils.data import DataLoader
from transformers import BertConfig

# -------------------------------------------------------------------------------
# Name:         trainDssm
# Description:
# Author:       lenovo
# Date:         2020/9/11
# -------------------------------------------------------------------------------
from dssm.data_process import *
from dssm.model_torch import *


def saveModel(model, file_path):
    print('Model save {} , {}'.format(file_path, time.asctime()))
    torch.save(model, file_path)
    # self.model.to(self.device)


BASE_DATA_PATH = './data/'

if __name__ == '__main__':
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
        dataset = pd.read_csv(sys.argv[2])
    else:
        BASE_DATA_PATH = '../data/'
        config_path = '../data/config.json_ab_1'
        dataset = pd.read_csv('../data/tt.csv')  # processed_train.csv

    config = BertConfig.from_pretrained(config_path)
    vocab = pickle.load(open(BASE_DATA_PATH + '/' + config.vocab_name, 'rb'))

    if '-1' not in config.gpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = config.gpu
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = 'cpu'

    print(' begin train ')

    if 'pt' in config.reload:
        model = torch.load(BASE_DATA_PATH + '/model/' + config.reload).to(device)
    else:
        if config.id == 1:
            model = DSSMOne(config, device).to(device)
            print('model_1')
        elif config.id == 2:
            model = DSSMTwo(config, device).to(device)
            print('model_2')
        elif config.id == 3:
            model = DSSMThree(config, device).to(device)
            print('model_3')
        elif config.id == 4:
            model = DSSMFour(config, device).to(device)
            print('model_4')
        elif config.id == 5:
            model = DSSMFive(config).to(device)
            print('model_5')
        elif config.id == 6:
            model = DSSMSix(config, device, vocab).to(device)
            print('model_6')
        elif config.id == 7:
            model = DSSMSeven(config).to(device)
            print('model_7')
        elif config.id == 8:
            model = DSSMEight(config).to(device)
            print('model_8')
        elif config.id == 9:
            model = DSSMNine(config).to(device)
            print('model_9')
        elif config.id == 'ab1':
            model = DSSMAbcnn1(config).to(device)
            print('model_ab1')

        print('para init')
        for m in model.modules():
            if isinstance(m, (nn.Conv1d, nn.Linear)):
                nn.init.xavier_uniform_(m.weight)
                print('para init', m.weight.shape, m.weight)
                # nn.init.kaiming_normal_(m.weight, mode='fan_in')

    ###损失函数定义
    if config.loss == 'bce':
        criterion = torch.nn.BCEWithLogitsLoss().to(device)  ###需要调整 网络结构
    elif config.loss == 'cross':
        criterion = torch.nn.CrossEntropyLoss().to(device)
    elif config.loss == 'mse':
        criterion = torch.nn.MSELoss().to(device)
    else:
        criterion = torch.nn.BCELoss().to(device)

    ###优化器定义
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, amsgrad=True)

    kf = KFold(n_splits=20, shuffle=True)
    best_loss = 100000
    for ll_ in range(config.nums + 1):
        for k, (train_index, val_index) in enumerate(kf.split(range(len(dataset)))):

            train = dataset.iloc[train_index]
            val = dataset.iloc[val_index]

            train_base = DSSMCharDataset(train, vocab, config)
            val = DSSMCharDataset(val, vocab, config)
            val = DataLoader(val, batch_size=config.batch_size, num_workers=2)

            print('Start train {} ford {}'.format(k, len(train_base)))

            stop_theld = 0  # >3 stop
            stop_value = 0.05
            old_total = best_loss

            for n_ in range(5 + 1):  # Epoch
                train = DataLoader(train_base, batch_size=config.batch_size, shuffle=True)

                total_loss = 0
                model.train()

                for i, data_set in enumerate(train):

                    data = {key: value.to(device) for key, value in data_set.items() if key != 'origin_'}
                    optimizer.zero_grad()
                    y_pred = model(data)
                    b_, _ = y_pred.shape

                    if config.loss == 'bce' or config.loss == 'mse':
                        tmp_ = torch.ones(b_).to(device).view(b_, -1) - data['label_'].view(b_, -1)
                        # y_target = torch.cat((tmp_, data['label_'].view(b_, -1).float()), dim=1)
                        # y_target = data['label_'].view(b_, -1).float()
                        loss = criterion(y_pred, tmp_)
                        # loss = criterion(y_pred.view(b_, -1), data['label_'].view(b_, -1))
                    elif config.loss == 'cross':
                        loss = criterion(y_pred, data['label_'])
                    else:
                        tmp_ = torch.ones(b_).to(device).view(b_, -1) - data['label_'].view(b_, -1)
                        y_target = torch.cat((tmp_, data['label_'].view(b_, -1).float()), dim=1)
                        loss = criterion(y_pred, y_target)

                    loss.backward()
                    optimizer.step()

                    if i % 20 == 0:
                        print(y_pred.data[0:5])
                        print('k ford and nums ,{} ,{},loss is {}'.format(n_, i, loss.data.item()))
                        for name, parms in model.named_parameters():
                            print('-->name:', name, '\t\t-->grad_requirs:', parms.requires_grad)
                            if parms.requires_grad and parms.grad is not None:
                                print('--weight', torch.mean(parms.data),
                                      '\t\t-->grad_value:', torch.mean(parms.grad), '\n')
                        print('\n\n')

                    total_loss += loss.data.item()

                    if i % 10 == 0:

                        with torch.no_grad():
                            model.eval()
                            loss_val = 0
                            for v_, data_set in enumerate(val):
                                data = {key: value.to(device) for key, value in data_set.items() if key != 'origin_'}
                                v_pred = model(data)
                                b_, _ = v_pred.shape

                                if config.loss == 'bce' or config.loss == 'mse':
                                    tmp_ = torch.ones(b_).to(device).view(b_, -1) - data['label_'].view(b_, -1)
                                    # y_target = torch.cat((tmp_, data['label_'].view(b_, -1).float()), dim=1)
                                    # y_target = data['label_'].view(b_, -1).float()
                                    loss = criterion(v_pred, tmp_)
                                elif config.loss == 'cross':
                                    loss = criterion(v_pred, data['label_'])
                                else:
                                    tmp_ = torch.ones(b_).to(device).view(b_, -1) - data['label_'].view(b_, -1)
                                    y_target = torch.cat((tmp_, data['label_'].view(b_, -1).float()), dim=1)
                                    loss = criterion(v_pred, y_target)

                                loss_val += loss

                            if best_loss > loss_val:
                                best_loss = loss_val
                                saveModel(model, BASE_DATA_PATH + 'model/{}_best_model_{}_{}_{}_{}_{}_ford.pt'.format(
                                    config.pre_info, config.segment_type, config.id, k, n_, i))
                                print('Save Best val loss _{}_{}_{}_{}_{}'.format(best_loss, config.id, k, n_, i))

                        model.train()

                print('total_loss ford and epochs ,{} ,{} ,{},loss is {}'.format(ll_, k, n_, total_loss))

                if abs(total_loss - old_total) <= stop_value:
                    stop_theld += 1
                    if stop_theld >= 3:
                        print('Stop Early_{}_{}_{}'.format(k, n_, i))
                        break
                    old_total = total_loss
