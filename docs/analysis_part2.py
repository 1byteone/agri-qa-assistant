def generate_html_report(year, df_cleaned, analysis_results, output_path):
    """生成纯HTML分析报告，包含Chart.js饼图"""
    year_str = str(year)
    year_data = analysis_results.get(year_str, {})
    
    production = year_data.get('production', {})
    area = year_data.get('area', {})
    
    total_production = sum(production.values()) if production else 0
    total_area = sum(area.values()) if area else 0
    
    production_labels = list(production.keys())
    production_values = list(production.values())
    area_labels = list(area.keys())
    area_values = list(area.values())
    
    colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40',
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'
    ]
    
    # Build HTML using string concatenation to avoid escaping issues
    html_lines = []
    html_lines.append('<!DOCTYPE html>')
    html_lines.append('<html lang="zh-CN">')
    html_lines.append('<head>')
    html_lines.append('    <meta charset="UTF-8">')
    html_lines.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_lines.append(f'    <title>{year}年种植业数据分析报告</title>')
    html_lines.append('    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')
    html_lines.append('    <style>')
    html_lines.append('        body { font-family: \'Microsoft YaHei\', sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f7fa; }')
    html_lines.append('        .header { text-align: center; padding: 30px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 30px; }')
    html_lines.append('        .header h1 { margin: 0; font-size: 2.5em; }')
    html_lines.append('        .section { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }')
    html_lines.append('        .section h2 { color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; margin-top: 0; }')
    html_lines.append('        .charts-container { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin: 30px 0; }')
    html_lines.append('        @media (max-width: 768px) { .charts-container { grid-template-columns: 1fr; } }')
    html_lines.append('        .chart-box { position: relative; height: 400px; background: #fafafa; padding: 20px; border-radius: 8px; }')
    html_lines.append('        table { width: 100%; border-collapse: collapse; margin: 20px 0; }')
    html_lines.append('        th, td { border: 1px solid #ddd; padding: 12px; text-align: center; }')
    html_lines.append('        th { background-color: #667eea; color: white; }')
    html_lines.append('        tr:nth-child(even) { background-color: #f2f2f2; }')
    html_lines.append('        .summary-box { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }')
    html_lines.append('        .summary-item { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }')
    html_lines.append('        .summary-item .value { font-size: 2em; font-weight: bold; margin: 10px 0; }')
    html_lines.append('        .interpretation { background: #fff3cd; padding: 20px; border-left: 4px solid #ffc107; border-radius: 5px; margin-top: 20px; }')
    html_lines.append('    </style>')
    html_lines.append('</head>')
    html_lines.append('')
    html_lines.append('<body>')
    html_lines.append('    <div class="header">')
    html_lines.append(f'        <h1>{year}年种植业数据分析报告</h1>')
    html_lines.append(f'        <p>基于{len(df_cleaned)}条清洗后数据的结构分析</p>')
    html_lines.append('    </div>')
    html_lines.append('')
    html_lines.append('    <div class="section">')
    html_lines.append('        <h2>📊 数据概览</h2>')
    html_lines.append('        <div class="summary-box">')
    html_lines.append('            <div class="summary-item">')
    html_lines.append('                <div>原始记录数</div>')
    html_lines.append(f'                <div class="value" id="raw-count">{len(df_raw)}</div>')
    html_lines.append('                <div>行</div>')
    html_lines.append('            </div>')
    html_lines.append('            <div class="summary-item">')
    html_lines.append('                <div>清洗后记录数</div>')
    html_lines.append(f'                <div class="value clean-data-count">{len(df_cleaned)}</div>')
    html_lines.append('                <div>行</div>')
    html_lines.append('            </div>')
    html_lines.append('        </div>')
    html_lines.append('        ')
    html_lines.append('        <h3>产量统计</h3>')
    html_lines.append('        <table>')
    html_lines.append('            <thead>')
    html_lines.append('                <tr>')
    html_lines.append('                    <th>作物类型</th>')
    html_lines.append('                    <th>产量（吨）</th>')
    html_lines.append('                    <th>占比</th>')
    html_lines.append('                </tr>')
    html_lines.append('            </thead>')
    html_lines.append('            <tbody>')
    
    # Add production rows
    for crop, prod in production.items():
        pct = (prod / total_production * 100) if total_production > 0 else 0
        html_lines.append(f'                <tr>')
        html_lines.append(f'                    <td>{crop}</td>')
        html_lines.append(f'                    <td>{prod:,.2f}</td>')
        html_lines.append(f'                    <td>{pct:.2f}%</td>')
        html_lines.append('                </tr>')
    
    # Add total row
    html_lines.append('                <tr>')
    html_lines.append('                    <th>总计</th>')
    html_lines.append(f'                    <th>{total_production:,.2f}</th>')
    html_lines.append('                    <th>100%</th>')
    html_lines.append('                </tr>')
    html_lines.append('            </tbody>')
    html_lines.append('        </table>')
    html_lines.append('        ')
    html_lines.append('        <h3>种植面积统计</h3>')
    html_lines.append('        <table>')
    html_lines.append('            <thead>')
    html_lines.append('                <tr>')
    html_lines.append('                    <th>作物类型</th>')
    html_lines.append('                    <th>种植面积（亩）</th>')
    html_lines.append('                    <th>占比</th>')
    html_lines.append('                </tr>')
    html_lines.append('            </thead>')
    html_lines.append('            <tbody>')
    
    # Add area rows
    for crop, area_val in area.items():
        pct = (area_val / total_area * 100) if total_area > 0 else 0
        html_lines.append(f'                <tr>')
        html_lines.append(f'                    <td>{crop}</td>')
        html_lines.append(f'                    <td>{area_val:,.2f}</td>')
        html_lines.append(f'                    <td>{pct:.2f}%</td>')
        html_lines.append('                </tr>')
    
    # Add total row for area
    html_lines.append('                <tr>')
    html_lines.append('                    <th>总计</th>')
    html_lines.append(f'                    <th>{total_area:,.2f}</th>')
    html_lines.append('                    <th>100%</th>')
    html_lines.append('                </tr>')
    html_lines.append('            </tbody>')
    html_lines.append('        </table>')
    html_lines.append('    </div>')
    html_lines.append('')
    html_lines.append('    <div class="section">')
    html_lines.append('        <h2>📈 作物结构分析</h2>')
    html_lines.append('        <div class="charts-container">')
    html_lines.append('            <div class="chart-box">')
    html_lines.append('                <h3>产量结构比例（饼图）</h3>')
    html_lines.append('                <canvas id="productionChart"></canvas>')
    html_lines.append('            </div>')
    html_lines.append('            <div class="chart-box">')
    html_lines.append('                <h3>种植面积比例（饼图）</h3>')
    html_lines.append('                <canvas id="areaChart"></canvas>')
    html_lines.append('            </div>')
    html_lines.append('        </div>')
    html_lines.append('        ')
    html_lines.append('        <div class="interpretation">')
    html_lines.append('            <strong>📝 解读：</strong>')
    html_lines.append(f'            <p>从图中可以看出，{year}年农业生产中，</p>')
    html_lines.append('            <ul>')
    html_lines.append('                <li><strong>粮食作物</strong>在产量结构中占据重要地位，是保障粮食安全的基础</li>')
    html_lines.append('                <li><strong>经济作物</strong>如蔬菜、水果、棉花等的种植面积和产量持续增长，反映了市场需求的变化</li>')
    html_lines.append('                <li><strong>其他作物</strong>作为补充，丰富了农业产业结构</li>')
    html_lines.append('            </ul>')
    html_lines.append('            <p>通过对比产量结构和种植面积比例，可以发现不同作物的产出效益差异，为农业结构调整提供数据支持。</p>')
    html_lines.append('        </div>')
    html_lines.append('    </div>')
    html_lines.append('')
    html_lines.append('    <script>')
    html_lines.append('        // 产量饼图')
    html_lines.append('        const productionCtx = document.getElementById(\'productionChart\').getContext(\'2d\');')
    production_colors = colors[:len(production_labels)]
    html_lines.append('        new Chart(productionCtx, {')
    html_lines.append('            type: \'pie\',')
    html_lines.append('            data: {')
    html_lines.append(f'                labels: {json.dumps(production_labels)},')
    html_lines.append('                datasets: [{')
    html_lines.append('                    label: \'产量（吨）\',')
    html_lines.append(f'                    data: {json.dumps(production_values)},')
    html_lines.append(f'                    backgroundColor: {json.dumps(production_colors)},')
    html_lines.append('                    borderWidth: 1')
    html_lines.append('                }]')
    html_lines.append('            },')
    html_lines.append('            options: {')
    html_lines.append('                responsive: true,')
    html_lines.append('                maintainAspectRatio: false,')
    html_lines.append('                plugins: {')
    html_lines.append('                    legend: { position: \'right\' },')
    html_lines.append('                    tooltip: {')
    html_lines.append('                        callbacks: {')
    html_lines.append('                            label: function(context) {')
    html_lines.append('                                return context.label + \': \' + context.parsed.toLocaleString(\'zh-CN\') + \' 吨 (\' + ((context.parsed / total_production * 100).toFixed(2)) + '%\');')
    html_lines.append('                            }')
    html_lines.append('                        }')
    html_lines.append('                    }')
    html_lines.append('                }')
    html_lines.append('            }')
    html_lines.append('        });')
    html_lines.append('')
    html_lines.append('        // 面积饼图')
    html_lines.append('        const areaCtx = document.getElementById(\'areaChart\').getContext(\'2d\');')
    area_colors = colors[:len(area_labels)]
    html_lines.append('        new Chart(areaCtx, {')
    html_lines.append('            type: \'pie\',')
    html_lines.append('            data: {')
    html_lines.append(f'                labels: {json.dumps(area_labels)},')
    html_lines.append('                datasets: [{')
    html_lines.append('                    label: \'种植面积（亩）\',')
    html_lines.append(f'                    data: {json.dumps(area_values)},')
    html_lines.append(f'                    backgroundColor: {json.dumps(area_colors)},')
    html_lines.append('                    borderWidth: 1')
    html_lines.append('                }]')
    html_lines.append('            },')
    html_lines.append('            options: {')
    html_lines.append('                responsive: true,')
    html_lines.append('                maintainAspectRatio: false,')
    html_lines.append('                plugins: {')
    html_lines.append('                    legend: { position: \'right\' },')
    html_lines.append('                    tooltip: {')
    html_lines.append('                        callbacks: {')
    html_lines.append('                            label: function(context) {')
    html_lines.append('                                return context.label + \': \' + context.parsed.toLocaleString(\'zh-CN\') + \' 亩 (\' + ((context.parsed / total_area * 100).toFixed(2)) + '%\');')
    html_lines.append('                            }')
    html_lines.append('                        }')
    html_lines.append('                    }')
    html_lines.append('                }')
    html_lines.append('            }')
    html_lines.append('        });')
    html_lines.append('    </script>')
    html_lines.append('')
    html_lines.append('</body>')
    html_lines.append('</html>')
    
    html_content = '\n'.join(html_lines) + '\n'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path


def main():
    """主执行函数"""
    data_path = r'd:\code\codeByCursor\AI_EXAM\data\2024年种植业数据.csv'
    
    # 读取原始数据
    print("正在读取原始数据...")
    df_raw = load_data(data_path)
    print(f"✓ 原始数据行数: {len(df_raw)}")
    
    # 获取唯一年份
    years = sorted(df_raw['年份'].unique().astype(str).tolist())
    print(f"✓ 检测到年份: {years}")
    
    # 处理每一年数据
    all_analysis_results = {}
    
    for year in years:
        print(f"\n--- 处理 {year}年数据 ---")
        
        # 过滤指定年份数据
        df_year = df_raw[df_raw['年份'] == str(year)].copy()
        print(f"  原始行数: {len(df_year)}")
        
        # 数据清洗
        df_cleaned = clean_data(df_year)
        print(f"  清洗后行数: {len(df_cleaned)}")
        
        # 结构分析
        analysis_results = analyze_structure(df_cleaned)
        
        # 保存分析结果
        all_analysis_results[str(year)] = {
            'df_cleaned': df_cleaned,
            'analysis': analysis_results
        }
        
        # 生成报告
        output_path = f'report_{year}.html'
        generate_html_report(year, df_cleaned, analysis_results, output_path)
        print(f"  ✓ 报告已生成: {output_path}")
    
    # 保存分析结果用于后续查看
    with open('analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(all_analysis_results, f, ensure_ascii=False, indent=2)
    print(f"\n✓ 分析结果已保存至 analysis_results.json")
    
    print(f"\n{'='*50}")
    print(f"任务完成！生成了以下文件:")
    for year in years:
        print(f"  - report_{year}.html")
    print(f"  - analysis.py (本文件)")
    print(f"  - analysis_results.json")
    print(f"{'='*50}")


if __name__ == '__main__':
    main()