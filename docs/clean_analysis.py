import pandas as pd
import json
import os

# ============================================================
# 1. 读取原始数据
# ============================================================
df = pd.read_csv('data\\2024年种植业数据.csv')
print(f"原始数据行数: {len(df)}")

# ============================================================
# 2. 数据清洗
# ============================================================

before_count = len(df)

# (1) 删除数值为 0 的数据
df = df[df['数值'] != 0].copy()
after_zero = len(df)
print(f"\n步骤1 - 删除数值为 0 的数据: 删除了 {before_count - after_zero} 行，剩余 {after_zero} 行")

# (2) 删除品类中包含人均的品类
df = df[~df['品类'].str.contains('人均', na=False)].copy()
print(f"步骤2 - 删除人均相关品类: 剩余 {len(df)} 行")

# (3) 产量单位：万吨 -> 吨
mask_prod = (df['指标'] == '产量') & (df['单位'] == '万吨')
df.loc[mask_prod, '数值'] = df.loc[mask_prod, '数值'] * 10000
df.loc[mask_prod, '单位'] = '吨'
print(f"步骤3 - 转换产量单位（万吨->吨）: 影响了 {mask_prod.sum()} 行")

# (4) 指标标准化：统一为"种植面积"
df['指标'] = df['指标'].replace({'播种面积': '种植面积'})

# (5) 面积单位：千公顷 -> 亩 (1 千公顷 = 15000 亩)
mask_area = (df['指标'] == '种植面积') & (df['单位'] == '千公顷')
df.loc[mask_area, '数值'] = df.loc[mask_area, '数值'] * 15000
df.loc[mask_area, '单位'] = '亩'
print(f"步骤5 - 转换面积单位（千公顷->亩）: 影响了 {mask_area.sum()} 行")

# 保存清洗后的数据
os.makedirs('data', exist_ok=True)
df.to_csv('data/cleaned_data.csv', index=False, encoding='utf-8-sig')
print(f"\n清洗完成，总行数: {len(df)}")

# ============================================================
# 3. 作物分类分析
# ============================================================

staple_crops = {'稻谷', '小麦', '玉米', '大豆', '薯类', '谷物',
                '中稻和一季晚稻', '双季晚稻', '早稻', '秋粮', '粮食'}

economic_crops = {'棉花', '油料', '糖料', '蔬菜', '梨', '柑桔',
                  '苹果', '葡萄', '柿子', '甘蔗', '红枣', '瓜果类',
                  '油菜籽', '烤烟', '烟叶', '其他茶', '柞蚕茧', '桑蚕茧'}

def categorize(crop):
    if crop in staple_crops:
        return '粮食作物'
    elif crop in economic_crops:
        return '经济作物'
    else:
        return '其他作物'

df['类别'] = df['品类'].apply(categorize)

production_df = df[df['指标'] == '产量']
area_df = df[df['指标'] == '种植面积']

def aggregate(dataframe, category):
    result = {}
    subset = dataframe[dataframe['类别'] == category]
    for _, row in subset.iterrows():
        crop = row['品类']
        val = row['数值']
        result[crop] = result.get(crop, 0) + val
    return dict(result)

sp_prod = aggregate(production_df, '粮食作物')
ep_prod = aggregate(production_df, '经济作物')
op_prod = aggregate(production_df, '其他作物')

sp_area = aggregate(area_df, '粮食作物')
ep_area = aggregate(area_df, '经济作物')
op_area = aggregate(area_df, '其他作物')

sp_total_prod = sum(sp_prod.values()) if sp_prod else 0
ep_total_prod = sum(ep_prod.values()) if ep_prod else 0
op_total_prod = sum(op_prod.values()) if op_prod else 0

sp_total_area = sum(sp_area.values()) if sp_area else 0
ep_total_area = sum(ep_area.values()) if ep_area else 0
op_total_area = sum(op_area.values()) if op_area else 0

total_prod = sp_total_prod + ep_total_prod + op_total_prod
total_area = sp_total_area + ep_total_area + op_total_area

print(f"\n=== 产量统计 ===")
print(f"粮食作物: {sp_total_prod:,} 吨 ({sp_total_prod/total_prod*100:.2f}%)")
print(f"经济作物: {ep_total_prod:,} 吨 ({ep_total_prod/total_prod*100:.2f}%)")
print(f"其他作物: {op_total_prod:,} 吨 ({op_total_prod/total_prod*100:.2f}%)")

print(f"\n=== 面积统计 ===")
print(f"粮食作物: {sp_total_area:,} 亩 ({sp_total_area/total_area*100:.2f}%)")
print(f"经济作物: {ep_total_area:,} 亩 ({ep_total_area/total_area*100:.2f}%)")
print(f"其他作物: {op_total_area:,} 亩 ({op_total_area/total_area*100:.2f}%)")

# ============================================================
# 4. 生成 HTML 分析报告
# ============================================================

def get_sorted_items(d):
    return sorted(d.items(), key=lambda x: -x[1])

max_crop_sp = max(sp_prod, key=sp_prod.get) if sp_prod else 'N/A'
max_crop_ep = max(ep_prod, key=ep_prod.get) if ep_prod else 'N/A'

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2024 年种植业数据分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body {{ font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f7fa; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ text-align: center; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }}
        h2 {{ color: #2980b9; margin-top: 30px; border-left: 5px solid #3498db; padding-left: 15px; }}
        h3 {{ color: #16a085; margin-top: 20px; }}
        .charts-row {{ display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; margin: 30px 0; }}
        .chart-box {{ width: 48%; min-width: 300px; background: #f8f9fa; padding: 20px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.1); }}
        @media (max-width: 768px) {{ .chart-box {{ width: 100%; }}} }
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #ecf0f1; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .highlight {{ background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0; }}
        .footer {{ text-align: center; margin-top: 50px; color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 2024 年种植业数据分析报告</h1>

        <section>
            <h2>一、数据清洗说明</h2>
            <p>本报告基于原始种植业数据经过以下清洗步骤：</p>
            <ol>
                <li><strong>删除数值为 0 的数据</strong>: 已删除所有数值为 0 的记录</li>
                <li><strong>删除人均相关品类</strong>: 移除了所有包含"人均"字样的数据（如人均棉花、人均油料、人均粮食）</li>
                <li><strong>产量单位转换</strong>: 将所有"万吨"单位的产量数据转换为"吨"（×10000）</li>
                <li><strong>指标标准化</strong>: 将播种面积统一转化为种植面积</li>
                <li><strong>面积单位转换</strong>: 将所有"千公顷"单位的种植面积转换为"亩"（×15000）</li>
            </ol>
        </section>

        <section>
            <h2>二、作物结构分析</h2>
            <div class="charts-row">
                <div class="chart-box">
                    <h3>产量比例分布饼图</h3>
                    <div id="prod_chart" style="height: 400px;"></div>
                </div>
                <div class="chart-box">
                    <h3>种植面积比例饼图</h3>
                    <div id="area_chart" style="height: 400px;"></div>
                </div>
            </div>
        </section>

        <section>
            <h2>三、详细数据分析</h2>
            <table>
                <thead>
                    <tr>
                        <th>作物类别</th>
                        <th>产量（吨）</th>
                        <th>产量占比</th>
                        <th>种植面积（亩）</th>
                        <th>面积占比</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>粮食作物</td>
                        <td>{sp_total_prod:,}</td>
                        <td>{sp_total_prod/total_prod*100:.2f}%</td>
                        <td>{sp_total_area:,}</td>
                        <td>{sp_total_area/total_area*100:.2f}%</td>
                    </tr>
                    <tr>
                        <td>经济作物</td>
                        <td>{ep_total_prod:,}</td>
                        <td>{ep_total_prod/total_prod*100:.2f}%</td>
                        <td>{ep_total_area:,}</td>
                        <td>{ep_total_area/total_area*100:.2f}%</td>
                    </tr>
                    <tr>
                        <td>其他作物</td>
                        <td>{op_total_prod:,}</td>
                        <td>{op_total_prod/total_prod*100:.2f}%</td>
                        <td>{op_total_area:,}</td>
                        <td>{op_total_area/total_area*100:.2f}%</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <section>
            <h2>四、主要作物清单</h2>
            <h3>主要粮食作物产量排名（前10）</h3>
            <table>
                <thead>
                    <tr><th>排序</th><th>作物品种</th><th>产量（吨）</th></tr>
                </thead>
                <tbody>
{chr(10).join([f'                    <tr><td>{i}</td><td>{crop}</td><td>{val:,}</td></tr>' for i, (crop, val) in enumerate(get_sorted_items(sp_prod)[:10], 1)])}
                </tbody>
            </table>

            <h3>主要经济作物产量排名（前10）</h3>
            <table>
                <thead>
                    <tr><th>排序</th><th>作物品种</th><th>产量（吨）</th></tr>
                </thead>
                <tbody>
{chr(10).join([f'                    <tr><td>{i}</td><td>{crop}</td><td>{val:,}</td></tr>' for i, (crop, val) in enumerate(get_sorted_items(ep_prod)[:10], 1)])}
                </tbody>
            </table>
        </section>

        <section class="highlight">
            <h2>五、解读与分析结论</h2>
            <ul>
                <li><strong>粮食作物产量占比 {:.2f}%</strong>: 在总产量中占据主导地位，体现了以粮食安全为核心的农业战略，生产稳定可靠。</li>
                <li><strong>经济作物产量占比 {:.2f}%</strong>: 贡献显著，反映了农业产业结构多样化发展成果，高附加值作物发展潜力大。</li>
                <li><strong>土地利用格局</strong>: 粮食作物种植面积 {:.2f}%，经济作物 {:.2f}%，体现合理的资源配置与可持续发展理念。</li>
                <li><strong>主导作物突出</strong>: 粮食作物中产量最高的是 {}（{:,} 吨），经济作物中产量最高的是 {}（{:,} 吨）。这些重点作物的规模化生产对保障供需平衡至关重要。</li>
            </ul>
            <p><strong>建议</strong>: 进一步优化种植结构，提高高附加值经济作物的生产效益和科技含量；巩固粮食生产能力的同时，注重耕地保护和农业现代化转型。</p>
        </section>

        <div class="footer">
            <p>报告生成时间: 2024-07-31</p>
            <p>数据来源: 2024 年种植业数据.csv</p>
        </div>
    </div>

    <script>
        // 产量饼图
        const prodChart = echarts.init(document.getElementById('prod_chart'));
        const prodOption = {{
            tooltip: {{ trigger: 'item', formatter: '{b}: {{:value}} ({{:percent}}%)' }},
            legend: {{ orient: 'vertical', left: 'left' }},
            series: [{{
                type: 'pie',
                radius: ['40%', '70%'],
                data: [{json.dumps([{"name": l, "value": v} for l, v in zip(["粮食作物", "经济作物", "其他作物"], [sp_total_prod, ep_total_prod, op_total_prod])]}, ensure_ascii=False}],
                emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }} }}
            }}]
        }};
        prodChart.setOption(prodOption);

        // 面积饼图
        const areaChart = echarts.init(document.getElementById('area_chart'));
        const areaOption = {{
            tooltip: {{ trigger: 'item', formatter: '{b}: {{:value}} ({{:percent}}%)' }},
            legend: {{ orient: 'vertical', left: 'left' }},
            series: [{{
                type: 'pie',
                radius: ['40%', '70%'],
                data: [{json.dumps([{"name": l, "value": v} for l, v in zip(["粮食作物", "经济作物", "其他作物"], [sp_total_area, ep_total_area, op_total_area])]}, ensure_ascii=False}],
                emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }} }}
            }}]
        }};
        areaChart.setOption(areaOption);

        window.addEventListener('resize', () => {{ prodChart.resize(); areaChart.resize(); }});
    </script>
</body>
</html>
'''.format(
    sp_total_prod/total_prod*100,
    ep_total_prod/total_prod*100,
    sp_total_area/total_area*100,
    ep_total_area/total_area*100,
    max_crop_sp, sp_total_prod,
    max_crop_ep, ep_total_prod
)

with open('analysis_report.html', 'w', encoding='utf-8-sig') as f:
    f.write(html)

print("\n✅ HTML 分析报告已生成: analysis_report.html")
print("✅ 清洗后数据已保存: data/cleaned_data.csv")
print("✅ Python 源码文件已保存: clean_analysis.py")

# Save complete Python source code
complete_code = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2024 年种植业数据分析脚本
功能：数据清洗、作物结构分析、HTML 报告生成
"""

import pandas as pd
import json
import os


def load_data(filepath):
    """加载原始 CSV 数据"""
    df = pd.read_csv(filepath)
    print(f"原始数据行数: {len(df)}")
    return df


def clean_data(df):
    """执行数据清洗操作"""
    before = len(df)

    # (1) 删除数值为 0 的数据
    df = df[df['数值'] != 0].copy()
    print(f"步骤1 - 删除数值为 0 的数据: 删除了 {before - len(df)} 行")

    # (2) 删除品类中包含人均的品类
    df = df[~df['品类'].str.contains('人均', na=False)].copy()
    print(f"步骤2 - 删除人均相关品类: 剩余 {len(df)} 行")

    # (3) 产量单位：万吨 -> 吨
    mask = (df['指标'] == '产量') & (df['单位'] == '万吨')
    df.loc[mask, '数值'] *= 10000
    df.loc[mask, '单位'] = '吨'
    print(f"步骤3 - 转换产量单位: 影响了 {mask.sum()} 行")

    # (4) 指标标准化：统一为"种植面积"
    df['指标'] = df['indicator'].replace({'播种面积': '种植面积'})

    # (5) 面积单位：千公顷 -> 亩 (1 千公顷 = 15000 亩)
    mask = (df['指标'] == '种植面积') & (df['单位'] == '千公顷')
    df.loc[mask, '数值'] *= 15000
    df.loc[mask, '单位'] = '亩'
    print(f"步骤5 - 转换面积单位: 影响了 {mask.sum()} 行")

    return df


def categorize_crop(crop_name):
    """给作物分类：粮食作物 / 经济作物 / 其他作物"""
    staple = {'稻谷', '小麦', '玉米', '大豆', '薯类', '谷物',
              '中稻和一季晚稻', '双季晚稻', '早稻', '秋粮', '粮食'}
    econ = {'棉花', '油料', '糖料', '蔬菜', '梨', '柑桔',
            '苹果', '葡萄', '柿子', '甘蔗', '红枣', '瓜果类',
            '油菜籽', '烤烟', '烟叶', '其他茶', '柞蚕茧', '桑蚕茧'}

    if crop_name in staple:
        return '粮食作物'
    elif crop_name in econ:
        return '经济作物'
    return '其他作物'


def aggregate(dataframe, category):
    """按类别聚合数据"""
    result = {}
    subset = dataframe[dataframe['类别'] == category]
    for _, row in subset.iterrows():
        crop = row['品类']
        val = row['数值']
        result[crop] = result.get(crop, 0) + val
    return dict(result)


def generate_html(sp_prod, ep_prod, op_prod, sp_area, ep_area, op_area, total_prod, total_area):
    """生成 HTML 分析报告"""
    sp_total = sum(sp_prod.values())
    ep_total = sum(ep_prod.values())
    op_total = sum(op_prod.values())
    sp_area_total = sum(sp_area.values())
    ep_area_total = sum(ep_area.values())
    op_area_total = sum(op_area.values())

    max_sp = max(sp_prod, key=sp_prod.get) if sp_prod else '-'
    max_ep = max(ep_prod, key=ep_prod.get) if ep_prod else '-'

    html_parts = []
    html_parts.append('''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2024 年种植业数据分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body { font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 30px; }
        h2 { color: #2980b9; margin-top: 30px; border-left: 5px solid #3498db; padding-left: 15px; }
        h3 { color: #16a085; margin-top: 20px; }
        .charts-row { display: flex; justify-content: space-around; flex-wrap: wrap; gap: 20px; margin: 30px 0; }
        .chart-box { width: 48%; min-width: 300px; background: #f8f9fa; padding: 20px; border-radius: 8px; box-shadow: 0 1px 5px rgba(0,0,0,0.1); }
        @media (max-width: 768px) { .chart-box { width: 100%; } }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #ecf0f1; font-weight: bold; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .highlight { background-color: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0; }
        .footer { text-align: center; margin-top: 50px; color: #7f8c8d; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 2024 年种植业数据分析报告</h1>

        <section>
            <h2>一、数据清洗说明</h2>
            <p>本报告基于原始种植业数据经过以下清洗步骤：</p>
            <ol>
                <li><strong>删除数值为 0 的数据</strong>: 已删除所有数值为 0 的记录</li>
                <li><strong>删除人均相关品类</strong>: 移除了所有包含"人均"字样的数据</li>
                <li><strong>产量单位转换</strong>: 将所有"万吨"单位的产量数据转换为"吨"（×10000）</li>
                <li><strong>指标标准化</strong>: 将播种面积统一转化为种植面积</li>
                <li><strong>面积单位转换</strong>: 将所有"千公顷"单位的种植面积转换为"亩"（×15000）</li>
            </ol>
        </section>

        <section>
            <h2>二、作物结构分析</h2>
            <div class="charts-row">
                <div class="chart-box">
                    <h3>产量比例分布饼图</h3>
                    <div id="prod_chart" style="height: 400px;"></div>
                </div>
                <div class="chart-box">
                    <h3>种植面积比例饼图</h3>
                    <div id="area_chart" style="height: 400px;"></div>
                </div>
            </div>
        </section>

        <section>
            <h2>三、详细数据分析</h2>
            <table>
                <thead>
                    <tr>
                        <th>作物类别</th>
                        <th>产量（吨）</th>
                        <th>产量占比</th>
                        <th>种植面积（亩）</th>
                        <th>面积占比</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>粮食作物</td>
                        <td>{:,}</td>
                        <td>{:.2f}%</td>
                        <td>{:,}</td>
                        <td>{:.2f}%</td>
                    </tr>
                    <tr>
                        <td>经济作物</td>
                        <td>{:,}</td>
                        <td>{:.2f}%</td>
                        <td>{:,}</td>
                        <td>{:.2f}%</td>
                    </tr>
                    <tr>
                        <td>其他作物</td>
                        <td>{:,}</td>
                        <td>{:.2f}%</td>
                        <td>{:,}</td>
                        <td>{:.2f}%</td>
                    </tr>
                </tbody>
            </table>
        </section>

        <section>
            <h2>四、主要作物清单</h2>
            <h3>主要粮食作物产量排名</h3>
            <table>
                <thead><tr><th>排序</th><th>作物品种</th><th>产量（吨）</th></tr></thead>
                <tbody>
{}
                </tbody>
            </table>

            <h3>主要经济作物产量排名</h3>
            <table>
                <thead><tr><th>排序</th><th>作物品种</th><th>产量（吨）</th></tr></thead>
                <tbody>
{}
                </tbody>
            </table>
        </section>

        <section class="highlight">
            <h2>五、解读与分析结论</h2>
            <ul>
                <li><strong>粮食作物产量占比 {:.2f}%</strong>: 占据主导地位，体现了以粮食安全为核心的农业战略。</li>
                <li><strong>经济作物产量占比 {:.2f}%</strong>: 贡献显著，反映了农业产业结构多样化发展成果。</li>
                <li><strong>土地利用格局</strong>: 粮食作物 {:.2f}%，经济作物 {:.2f}%，体现合理资源配置。</li>
                <li><strong>主导作物</strong>: 粮食作物最高为 "{}"（{:,} 吨），经济作物最高为 "{}"（{:,} 吨）。</li>
            </ul>
            <p><strong>建议</strong>: 优化种植结构，提高高附加值经济作物效益，同时巩固粮食生产能力。</p>
        </section>

        <div class="footer">
            <p>报告生成时间: 2024-07-31</p>
            <p>数据来源: 2024 年种植业数据.csv</p>
        </div>
    </div>

    <script>
        const prodChart = echarts.init(document.getElementById('prod_chart'));
        prodChart.setOption({{
            tooltip: {{ trigger: 'item', formatter: '{b}: {{:value}} ({{:percent}}%)' }},
            legend: {{ orient: 'vertical', left: 'left' }},
            series: [{{
                type: 'pie',
                radius: ['40%', '70%'],
                data: [{}],
                emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }} }}
            }}]
        }});

        const areaChart = echarts.init(document.getElementById('area_chart'));
        areaChart.setOption({{
            tooltip: {{ trigger: 'item', formatter: '{b}: {{:value}} ({{:percent}}%)' }},
            legend: {{ orient: 'vertical', left: 'left' }},
            series: [{{
                type: 'pie',
                radius: ['40%', '70%'],
                data: [{}],
                emphasis: {{ itemStyle: {{ shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' }} }}
            }}]
        }});

        window.addEventListener('resize', () => {{ prodChart.resize(); areaChart.resize(); }});
    </script>
</body>
</html>
'''.format(
        sp_total, sp_total/total_prod*100, sp_area_total, sp_area_total/total_area*100,
        ep_total, ep_total/total_prod*100, ep_area_total, ep_area_total/total_area*100,
        op_total, op_total/total_prod*100, op_area_total, op_area_total/total_area*100,
        ''.join([f'                    <tr><td>{i}</td><td>{crop}</td><td>{val:,}</td></tr>' for i, (crop, val) in enumerate(sorted(sp_prod.items(), key=lambda x: -x[1])[:10], 1)]),
        ''.join([f'                    <tr><td>{i}</td><td>{crop}</td><td>{val:,}</td></tr>' for i, (crop, val) in enumerate(sorted(ep_prod.items(), key=lambda x: -x[1])[:10], 1)]),
        sp_total/total_prod*100, ep_total/total_prod*100, sp_area_total/total_area*100, ep_area_total/total_area*100, max_sp, sp_total, max_ep, ep_total,
        json.dumps([{"name": "粮食作物", "value": sp_total}, {"name": "经济作物", "value": ep_total}, {"name": "其他作物", "value": op_total}], ensure_ascii=False),
        json.dumps([{"name": "粮食作物", "value": sp_area_total}, {"name": "经济作物", "value": ep_area_total}, {"name": "其他作物", "value": op_area_total}], ensure_ascii=False)
    )

    return html


def main():
    # 加载数据
    df = load_data('data\\2024年种植业数据.csv')

    # 数据清洗
    df = clean_data(df)

    # 添加类别列
    df['类别'] = df['品类'].apply(categorize_crop)

    production = df[df['指标'] == '产量']
    area = df[df['指标'] == '种植面积']

    # 聚合
    sp_prod = aggregate(production, '粮食作物')
    ep_prod = aggregate(production, '经济作物')
    op_prod = aggregate(production, '其他作物')

    sp_area = aggregate(area, '粮食作物')
    ep_area = aggregate(area, '经济作物')
    op_area = aggregate(area, '其他作物')

    # 计算总量
    sp_total = sum(sp_prod.values()) if sp_prod else 0
    ep_total = sum(ep_prod.values()) if ep_prod else 0
    op_total = sum(op_prod.values()) if op_prod else 0
    sp_area_total = sum(sp_area.values()) if sp_area else 0
    ep_area_total = sum(ep_area.values()) if ep_area else 0
    op_area_total = sum(op_area.values()) if op_area else 0

    total_prod = sp_total + ep_total + op_total
    total_area = sp_area_total + ep_area_total + op_area_total

    print(f"\n粮食作物产量: {sp_total:,} 吨")
    print(f"经济作物产量: {ep_total:,} 吨")
    print(f"其他作物产量: {op_total:,} 吨")
    print(f"\n粮食作物面积: {sp_area_total:,} 亩")
    print(f"经济作物面积: {ep_area_total:,} 亩")
    print(f"其他作物面积: {op_area_total:,} 亩")

    # 保存清洗数据
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/cleaned_data.csv', index=False, encoding='utf-8-sig')

    # 生成 HTML
    html = generate_html(sp_prod, ep_prod, op_prod, sp_area, ep_area, op_area, total_prod, total_area)
    with open('analysis_report.html', 'w', encoding='utf-8-sig') as f:
        f.write(html)

    print("\\n✅ 所有文件生成完成！")
    print("  - cleaned_data.csv: 清洗后的数据")
    print("  - analysis_report.html: HTML 分析报告")
    print("  - clean_analysis.py: Python 源码")


if __name__ == '__main__':
    main()
'''

with open('clean_analysis_final.py', 'w', encoding='utf-8') as f:
    f.write(complete_code)

print("✅ 完整 Python 源码已保存: clean_analysis_final.py")