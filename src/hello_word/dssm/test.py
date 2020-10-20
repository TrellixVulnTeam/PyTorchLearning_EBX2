# -*- coding: utf-8 -*-#

# -------------------------------------------------------------------------------
# Name:         test
# Description:  
# Author:       lenovo
# Date:         2020/9/25
# -------------------------------------------------------------------------------

import os

######################################
from torch.utils.data import DataLoader

from dssm.data_process import *
from dssm.model_torch import *

os.environ["CUDA_VISIBLE_DEVICES"] = "0"
BASE_DATA_PATH = '../data/'
from transformers import BertConfig


def test():
    print('begin0')
    # os.environ["CUDA_VISIBLE_DEVICES"] = '2'
    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = 'cpu'

    print('begin')
    config_path = '../data/config.json_7'
    dataset = pd.read_csv('../data/test_avg_1.csv')  # processed_train.csv

    config = BertConfig.from_pretrained(config_path)

    vacab = pickle.load(open(BASE_DATA_PATH + '/' + config.vocab_name, 'rb'))
    data_base = DSSMCharDataset(dataset, vacab, config)  # same with the config_4
    data = DataLoader(data_base, batch_size=100)

    model = torch.load(BASE_DATA_PATH + 'model/name__best_model_char_7_8_0_3_ford.pt').to(device)

    with torch.no_grad():
        num_ = []
        for i, data_ in enumerate(data):
            y_pred = model(data_)
            b_, _ = y_pred.shape

            org_ = data_['origin_']
            label_ = data_['label_']

            if config.loss == 'cross':

                k_ = torch.max(y_pred, 1)[1]
                tmp_ = torch.cat((k_.float().unsqueeze(1), label_.float().unsqueeze(1)), dim=1)
                acc_ = sum(k_ == label_)

            else:
                t_pred = y_pred > 0.4
                t_label = label_.unsqueeze(1) == 0
                acc_ = sum(t_pred == t_label)
                # print(t_pred.shape, t_label.shape, acc_)

                tmp_ = torch.cat((t_pred.float(), t_label.float(), y_pred), dim=1)

            num_.append(float(acc_.item()) / b_)
            print(acc_.item(), b_, float(acc_.item()) / b_)

            for ii, d_ in enumerate(tmp_):
                if d_[0] != d_[1]:
                    print(org_[ii], label_[ii], tmp_[ii])
            #     if tmp_[ii][0] * tmp_[ii][1] > 0:
            #         print('Test , {} {}'.format(org_[ii], tmp_[ii]))

        print(num_, sum(num_) / len(num_))


from dssm.clusterProcess import model_init, sameLogic


def testSigle(s1, s2):
    model_dict, char_vocab, word_vocab, max_len, device = model_init()
    name_sim = sameLogic(s1, s2, model_dict, char_vocab, word_vocab, max_len, device)

    print(name_sim)


from dssm.clusterProcess import dataPro


def testOne(s1, s2):
    device = 'cpu'
    config_path = '../data/config.json_7'

    config = BertConfig.from_pretrained(config_path)
    model = torch.load(BASE_DATA_PATH + 'model/name__best_model_char_7_6_0_0_ford.pt').to(device)
    vacob = pickle.load(open(BASE_DATA_PATH + '/' + config.vocab_name, 'rb'))
    name_1, name_2 = dataPro(s1, s2, config.max_len, vacob)
    # print(name_1, name_2)
    with torch.no_grad():
        data_ = {'query_': torch.tensor(name_1).unsqueeze(0).to(device), 'doc_': torch.tensor(name_2).unsqueeze(0).to(device)}
        pred = model(data_)
        print(pred)
        k_ = torch.max(pred, 1)[1][0]
        print(k_.data.item())

        data_ = {'query_': torch.tensor(name_2).unsqueeze(0).to(device), 'doc_': torch.tensor(name_1).unsqueeze(0).to(device)}
        pred = model(data_)
        print(pred)
        k_ = torch.max(pred, 1)[1][0]
        print(k_.data.item())


from dssm.runData import distance_edit, distance_jacaard

if __name__ == '__main__':
    pass
    # test()
    s1 = ["AZIENDE RIUNITE CAFFE SPA VIA IPPOLITO ROSELLINI,2-20124 MILANO", 'NULL']
    s2 = ["ESSSE CAFFE SPA", 'NULL']

    testOne(s1[0], s2[0])

    # testSigle(s1, s2)

    print(distance_edit(s1[0], s2[0]))

    print(distance_jacaard(s1[0], s2[0]))
