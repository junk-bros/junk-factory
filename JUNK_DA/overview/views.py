from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import numpy as np
import pandas as pd
from pandas import DataFrame, Series


# Create your views here.


# 数据概览
class OverViews:

    # 非数值特征处理函数
    def _nonum_feature_process(self, df, dic, thresh_val=8):
        nonum_feature_dic = {}
        data_num = len(df)
        for feature in dic.keys():
            if dic[feature] == '非数值':
                _cls_arr = df[df[feature].notnull()][feature].unique()
                _cls_number = len(_cls_arr)

                # 类别个数过多情况
                if _cls_number > thresh_val:
                    nonum_feature_dic[feature] = {
                        '类别': '类别过多'
                    }

                    # 判断是否有缺失值
                    if df[feature].count() < data_num:
                        nonum_feature_dic[feature]['缺失值个数'] = int(
                            data_num - df[feature].count())

                # 类别个数小于阈值情况
                else:
                    cls_dic = {
                        _cls: int(df[feature].value_counts()[_cls])
                        for _cls in _cls_arr
                    }

                    # 判断是否有缺失值
                    if df[feature].count() < data_num:
                        cls_dic['缺失值个数'] = int(
                            data_num - df[feature].count())
                    nonum_feature_dic[feature] = cls_dic
        return nonum_feature_dic

    # 数值特征处理函数
    def _num_feature_process(self, df, dic, thresh_val=8):
        num_feature_dic = {}
        data_num = len(df)
        for feature in dic.keys():
            if dic[feature] == '数值':
                _cls_arr = df[df[feature].notnull()][feature].unique()
                _cls_number = len(_cls_arr)

                # 连续型
                if _cls_number > thresh_val:
                    num_feature_dic[feature] = {
                        '平均数': '%.1f' % df[feature].mean(),
                        # '众数': list(df[feature].mode()),
                        '分位数': '%.1f' % df[feature].median(),
                        '最大值': '%.1f' % df[feature].max(),
                        '最小值': '%.1f' % df[feature].min(),
                    }

                    # 判断是否有缺失值
                    if df[feature].count() < data_num:
                        num_feature_dic[feature]['缺失值个数'] = int(
                            data_num - df[feature].count())

                # 离散型
                else:
                    cls_dic = {
                        str(_cls): int(df[feature].value_counts()[_cls])
                        for _cls in _cls_arr
                    }

                    # 判断是否有缺失值
                    if df[feature].count() < data_num:
                        cls_dic['缺失值个数'] = int(
                            data_num - df[feature].count())
                    num_feature_dic[feature] = cls_dic
        return num_feature_dic

    # overview页面接口
    def overview(self, request):
        # 读取参数
        userId = request.GET.get('userId')
        filename = userId + request.GET.get('file')

        df = pd.read_csv(filename)
        dic = {}

        # 特征个数
        dic['featureNum'] = len(df.columns)

        # 数据个数
        dic['dataNum'] = len(df.index)

        # 特征类型
        type_dic = {}
        for column in df.columns:
            if df[column].dtypes == 'object':
                type_dic[column] = '非数值'
            else:
                type_dic[column] = '数值'
        dic['featureType'] = type_dic

        # 含缺失值特征
        feature_with_nan = [
            column for column in df.columns
            if not df[column][df[column].isnull()].empty
        ]
        if feature_with_nan:
            dic['featureWithNan'] = feature_with_nan

        # 非数值特征处理
        nonum_feature_dic = self._nonum_feature_process(df, dic['featureType'])
        if nonum_feature_dic:
            dic['noNumTypeFeature'] = nonum_feature_dic

        # 数值型特征处理
        num_feature_dic = self._num_feature_process(df, dic['featureType'])
        if num_feature_dic:
            dic['numTypeFeature'] = num_feature_dic

        dic = json.dumps(dic, ensure_ascii=False)
        return HttpResponse(dic)


# 分位数
class Quantile:
    def quant(self, request):
        # 读取参数
        userId = request.GET.get('userId')
        filename = userId + request.GET.get('file')
        qua_para = int(request.GET.get('quantile')) / 100
        col_para = request.GET.get('column')

        df = pd.read_csv(filename)
        qua_dic = {col_para: '%.1f' % df[col_para].quantile(qua_para)}
        qua_dic = json.dumps(qua_dic, ensure_ascii=False)
        return HttpResponse(qua_dic)
