# -*- coding: utf-8 -*-#

import time

import tqdm
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

    dataset = pd.read_csv(BASE_DATA_PATH + '/processed_train.csv')
    print('begin0')
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    config = BertConfig.from_pretrained(BASE_DATA_PATH + '/config.json')
    print('begin1')
    vacab = pickle.load(open(BASE_DATA_PATH + '/char2id.vocab', 'rb'))

    criterion = torch.nn.BCEWithLogitsLoss().to(device)

    print('begin')

    # for e in range(100):
    #     print('epoch %d', e)

    kf = KFold(n_splits=10, shuffle=True)
    nums_ = 50

    for k, (train_index, val_index) in enumerate(kf.split(range(len(dataset)))):
        print('Start train {} ford'.format(k))

        train = dataset.iloc[train_index]
        val = dataset.iloc[val_index]

        train_base = DSSMCharDataset(train, vacab)
        # train = DataLoader(train, batch_size=256, shuffle=True)
        val = DSSMCharDataset(val, vacab)
        val = DataLoader(val, batch_size=256, num_workers=2)

        model = DSSMOne(config, device).to(device)
        optimizer = torch.optim.SGD(model.parameters(), lr=1e-4, momentum=0.9)

        best_loss = 100000

        model.train()

        for i in range(nums_):
            print('k ford and nums ,{} ,{}'.format(k, i))
            train = DataLoader(train_base, batch_size=256, shuffle=True)

            data_loader = tqdm.tqdm(enumerate(train),
                                    total=len(train))
            for i, data_set in data_loader:
                data = {key: value.to(device) for key, value in data_set.items()}
                # print(data['query_'])

                y_pred = model(data)
                b_, _ = y_pred.shape

                loss = criterion(y_pred.view(b_, -1), data['label_'].view(b_, -1))

                optimizer.zero_grad()
                loss.backward()
                optimizer.step()

        with torch.no_grad():
            # model.eval()
            data_loader = tqdm.tqdm(enumerate(val),
                                    total=len(val))
            loss_val = 0
            for i, data_set in data_loader:
                data = {key: value.to(device) for key, value in data_set.items()}
                y_pred = model(data)
                b_, _ = y_pred.shape

                loss_val += criterion(y_pred.view(b_, -1), data['label_'].view(b_, -1))

            if best_loss > loss_val:
                best_loss = loss_val
                saveModel(model, BASE_DATA_PATH + '/best_model_{}ford.pt'.format(k))
                print('Best val loss {} ,{},{}'.format(best_loss, k, time.asctime()))

                # model.to(device)

        # trainer.load('best_model_{}ford.pt'.format(k))
        # for i in trainer.inference(val):
        #     print(i)
        #     print('\n')
