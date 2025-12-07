function initKlineDraw(containerId) {
    var myChart = echarts.init(document.getElementById(containerId));
    var keyPoints = [];

    var option = {
        title: { text: '交互式走势绘制', left: 'center' },
        tooltip: { trigger: 'axis' },
        // 新增：数据缩放（放大缩小）
        dataZoom: [
            { type: 'inside', xAxisIndex: 0 },
            { type: 'slider', xAxisIndex: 0 }
        ],
        grid: {
            left: '3%', right: '4%', bottom: '15%', containLabel: true
        },
        xAxis: { type: 'category', data: ['Day1', 'Day2', 'Day3', 'Day4', 'Day5', 'Day6', 'Day7'] },
        yAxis: [
            { type: 'value', name: '价格' },
            { type: 'value', name: 'MACD', min: -2, max: 2, position: 'right' }  // 新增MACD轴
        ],
        series: [
            {
                name: '价格', type: 'line', data: [10, 12, 9, 15, 11, 13, 10],
                markPoint: { data: [], symbolSize: 80, itemStyle: { color: 'red' } }
            },
            // 新增：叠加MACD指标
            {
                name: 'MACD', type: 'bar', yAxisIndex: 1,
                data: [0.2, -0.3, 0.5, -0.1, 0.4, 0.1, -0.2],
                itemStyle: { color: function(params) {
                    return params.value > 0 ? '#FF0000' : '#00FF00';
                }}
            }
        ]
    };
    myChart.setOption(option);

    // 监听鼠标点击事件，捕捉关键点位
    myChart.on('click', function(params) {
        var price = params.value[1];
        var date = params.name;
        keyPoints.push({
            'date': date,
            'price': price,
            'type': 'point'
        });
        // 更新标记点
        option.series[0].markPoint.data.push({
            name: date,
            value: price,
            xAxis: params.dataIndex,
            yAxis: price
        });
        myChart.setOption(option);
        console.log('已添加关键点位：', keyPoints);
    });

    // 暴露方法
    return {
        getKeyPoints: function() {
            return JSON.stringify(keyPoints);
        },
        clearPoints: function() {
            keyPoints = [];
            option.series[0].markPoint.data = [];
            myChart.setOption(option);
        }
    };
}