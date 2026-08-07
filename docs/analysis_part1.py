#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2023/2024年种植业数据分析脚本
功能：数据清洗、农作物结构分析、生成HTML分析报告
"""

import pandas as pd
import json
from pathlib import Path


def load_data(filepath):
    """加载CSV数据"""
    return pd.read_csv(filepath, encoding='utf-8')


def clean_data(df):
    """
    数据清洗：
    1. 删除数值为0的数据
    2. 删除品类中包含人均的品类
    3. 将指标为产量的数值单位中的万吨统一转换为吨
    4. 将指标为'播种面积/种植面积'统一转换为种植面积
    5. 将指标为种植的数值单位由千公顷转换为亩（1公顷=15亩）
    """
    # 步骤1: 删除数值为0的行
    df = df[df['数值'] != 0].copy()
    
    # 步骤2: 删除品类中包含"人均"的行
    df = df[~df['品类'].str.contains('人均', na=False)].copy()
    
    # 步骤3: 标准化指标名 - "播种面积/种植面积" -> "种植面积"
    df['指标'] = df['指标'].replace({'播种面积/种植面积': '种植面积'})
    
    # 步骤3a: 产量单位转换 - 万吨 -> 吨
    mask_production = (df['指标'] == '产量') & (df['单位'] == '万吨')
    df.loc[mask_production, '数值'] = df.loc[mask_production, '数值'] * 10000
    df.loc[mask_production, '单位'] = '吨'
    
    # 步骤3b: 面积单位转换 - 千公顷 -> 亩（1公顷=15亩）
    mask_area = df['指标'].str.contains('播种面积|种植面积', na=False) & (df['单位'] == '千公顷')
    df.loc[mask_area, '数值'] = df.loc[mask_area, '数值'] * 15
    df.loc[mask_area, '单位'] = '亩'
    
    return df


def classify_crop(crop_name):
    """
    作物分类：
    - 粮食作物: 水稻、小麦、玉米、大豆、薯类、谷物、稻谷、秋粮、粮食、中稻和一季晚稻、早稻、春小麦、冬小麦
    - 经济作物: 油料、棉花、糖料、蔬菜、水果、茶叶、烟叶、油菜籽、花生、烤烟、甘蔗、甜菜、瓜果类、苹果、葡萄、柑桔、柿子、红枣、香蕉、芝麻、果园、柑桔园、梨园
    - 其他作物: 向日葵籽、胡麻籽、红小豆、绿豆、豆类等
    """
    staple_crops = {
        '水稻', '小麦', '玉米', '大豆', '薯类', '谷物', '稻谷', '秋粮', '粮食',
        '中稻和一季晚稻', '早稻', '春小麦', '冬小麦', '双季晚稻'
    }
    
    economic_crops = {
        '油料', '棉花', '糖料', '蔬菜', '水果', '茶叶', '烟叶', '油菜籽', '花生',
        '烤烟', '甘蔗', '甜菜', '瓜果类', '苹果', '葡萄', '柑桔', '柿子', '红枣',
        '香蕉', '芝麻', '果园', '柑桔园', '梨园'
    }
    
    if crop_name in staple_crops:
        return '粮食作物'
    elif crop_name in economic_crops:
        return '经济作物'
    else:
        return '其他作物'


def analyze_structure(df):
    """
    按年份和作物类型进行结构分析
    返回: {year: {'产量': {crop: value}, '面积': {crop: value}}}
    """
    results = {}
    
    for year in sorted(df['年份'].unique()):
        year_df = df[df['年份'] == str(year)].copy()
        
        # 添加作物类型列
        year_df['作物类型'] = year_df['品类'].apply(classify_crop)
        
        # 聚合产量（吨）
        production_mask = (year_df['指标'] == '产量') & (year_df['单位'] == '吨')
        prod_by_type = year_df[production_mask].groupby('作物类型')['数值'].sum()
        
        # 聚合种植面积（亩）
        area_mask = year_df['指标'].str.contains('播种面积|种植面积', na=False) & (year_df['单位'] == '亩')
        area_by_type = year_df[area_mask].groupby('作物类型')['数值'].sum()
        
        results[str(year)] = {
            'production': {k: round(float(v), 2) for k, v in prod_by_type.items()},
            'area': {k: round(float(v), 2) for k, v in area_by_type.items()}
        }
    
    return results