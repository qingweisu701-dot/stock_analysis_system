// 数据采集
function crawlData() {
    $.ajax({
        url: '/crawl_data',
        type: 'POST',
        success: function(res) {
            if (res.code === 200) {
                alert(res.msg);
            } else {
                alert(res.msg);
            }
        },
        error: function(err) {
            alert('请求失败：' + err.statusText);
        }
    });
}

// 创建绘制型模板
var klineDraw;
$(function() {
    // 初始化K线绘制组件
    if ($('#kline_container').length > 0) {
        klineDraw = initKlineDraw('kline_container');
    }

    // 提交绘制型模板
    $('#drawPatternForm').submit(function(e) {
        e.preventDefault();
        var templateName = $('#templateName').val();
        var keyPoints = klineDraw.getKeyPoints();
        if (!templateName) {
            alert('请输入模板名称！');
            return;
        }
        $.ajax({
            url: '/create_draw_pattern',
            type: 'POST',
            data: {
                template_name: templateName,
                key_points: keyPoints
            },
            success: function(res) {
                if (res.code === 200) {
                    alert(res.msg);
                    $('#drawPatternForm')[0].reset();
                    klineDraw.clearPoints();
                } else {
                    alert(res.msg);
                }
            },
            error: function(err) {
                alert('请求失败：' + err.statusText);
            }
        });
    });

    // 提交表格型模板
    $('#tablePatternForm').submit(function(e) {
        e.preventDefault();
        var templateName = $('#tableTemplateName').val();
        var tableFile = $('#tableFile')[0].files[0];
        if (!templateName || !tableFile) {
            alert('请输入模板名称并选择表格文件！');
            return;
        }
        var formData = new FormData();
        formData.append('template_name', templateName);
        formData.append('table_file', tableFile);
        $.ajax({
            url: '/create_table_pattern',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(res) {
                if (res.code === 200) {
                    alert(res.msg);
                    $('#tablePatternForm')[0].reset();
                } else {
                    alert(res.msg);
                }
            },
            error: function(err) {
                alert('请求失败：' + err.statusText);
            }
        });
    });

    // 提交指标组合型模板
    $('#indicatorPatternForm').submit(function(e) {
        e.preventDefault();
        var templateName = $('#indicatorTemplateName').val();
        var indicatorConditions = $('#indicatorConditions').val();
        if (!templateName || !indicatorConditions) {
            alert('请输入模板名称和指标条件！');
            return;
        }
        $.ajax({
            url: '/create_indicator_pattern',
            type: 'POST',
            data: {
                template_name: templateName,
                indicator_conditions: indicatorConditions
            },
            success: function(res) {
                if (res.code === 200) {
                    alert(res.msg);
                    $('#indicatorPatternForm')[0].reset();
                } else {
                    alert(res.msg);
                }
            },
            error: function(err) {
                alert('请求失败：' + err.statusText);
            }
        });
    });

    // 获取所有模板并填充下拉框
    function loadPatterns() {
        $.ajax({
            url: '/get_patterns',
            type: 'GET',
            success: function(res) {
                if (res.code === 200) {
                    var patternSelect = $('#patternId');
                    patternSelect.empty();
                    res.data.forEach(function(pattern) {
                        patternSelect.append('<option value="' + pattern.id + '">' + pattern.template_name + '</option>');
                    });
                }
            }
        });
    }
    if ($('#patternId').length > 0) {
        loadPatterns();
    }

    // 相似模式匹配
    $('#matchPatternForm').submit(function(e) {
        e.preventDefault();
        var formData = $(this).serialize();
        $.ajax({
            url: '/match_pattern',
            type: 'POST',
            data: formData,
            success: function(res) {
                if (res.code === 200) {
                    var resultTable = $('#matchResult');
                    resultTable.empty();
                    // 生成表头
                    resultTable.append('<tr><th>股票代码</th><th>股票名称</th><th>所属行业</th><th>当前价格</th><th>总市值(亿元)</th><th>相似度</th></tr>');
                    // 填充数据
                    res.data.forEach(function(item) {
                        resultTable.append(
                            '<tr><td>' + item.ts_code + '</td><td>' + item.name + '</td><td>' + item.industry + '</td>' +
                            '<td>' + item.price + '</td><td>' + item.total_mv.toFixed(2) + '</td><td>' + item.similarity + '</td></tr>'
                        );
                    });
                } else {
                    alert(res.msg);
                }
            },
            error: function(err) {
                alert('请求失败：' + err.statusText);
            }
        });
    });

    // 买卖点预测
    $('#predictForm').submit(function(e) {
        e.preventDefault();
        var tsCode = $('#tsCode').val();
        var modelType = $('#modelType').val();
        if (!tsCode) {
            alert('请输入股票代码！');
            return;
        }
        $.ajax({
            url: '/predict_buy_sell',
            type: 'POST',
            data: {
                ts_code: tsCode,
                model_type: modelType
            },
            success: function(res) {
                if (res.code === 200) {
                    var resultDiv = $('#predictResult');
                    resultDiv.html(
                        '<p>股票代码：' + res.data.ts_code + '</p>' +
                        '<p>预测买点：' + res.data.buy_point + ' 元</p>' +
                        '<p>预测卖点：' + res.data.sell_point + ' 元</p>' +
                        '<p>建议持仓天数：' + res.data.hold_days + ' 天</p>' +
                        '<p>预测准确率：' + (res.data.accuracy * 100).toFixed(2) + '%</p>'
                    );
                } else {
                    alert(res.msg);
                }
            },
            error: function(err) {
                alert('请求失败：' + err.statusText);
            }
        });
    });

    // 回测
    $('#backtestForm').submit(function(e) {
        e.preventDefault();
        var tsCode = $('#backtestTsCode').val();
        var startDate = $('#startDate').val().replace(/-/g, '');
        var endDate = $('#endDate').val().replace(/-/g, '');
        var modelType = $('#backtestModelType').val();
        if (!tsCode || !startDate || !endDate) {
            alert('请填写完整回测参数！');
            return;
        }
        $.ajax({
            url: '/backtest',
            type: 'POST',
            data: {
                ts_code: tsCode,
                start_date: startDate,
                end_date: endDate,
                model_type: modelType
            },
            success: function(res) {
                if (res.code === 200) {
                    var resultDiv = $('#backtestResult');
                    resultDiv.html(
                        '<p>总交易次数：' + res.data.total_trades + '</p>' +
                        '<p>盈利次数：' + res.data.win_count + '</p>' +
                        '<p>胜率：' + (res.data.win_rate * 100).toFixed(2) + '%</p>' +
                        '<p>平均单次收益率：' + (res.data.avg_return * 100).toFixed(2) + '%</p>' +
                        '<p>累计收益率：' + (res.data.cumulative_return * 100).toFixed(2) + '%</p>' +
                        '<img src="/get_backtest_chart/' + res.data.chart_path + '" style="width:100%;margin-top:20px;">'
                    );
                } else {
                    alert(res.msg);
                }
            },
            error: function(err) {
                alert('请求失败：' + err.statusText);
            }
        });
    });
});