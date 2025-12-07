// static/js/api.js - 统一的API调用
class StockAPI {
    static baseURL = '/api';

    // 模式管理相关API
    static async getPatterns() {
        const response = await fetch(`${this.baseURL}/patterns`);
        return await response.json();
    }

    static async createPattern(patternData) {
        const response = await fetch(`${this.baseURL}/patterns`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(patternData)
        });
        return await response.json();
    }

    static async getPatternById(id) {
        const response = await fetch(`${this.baseURL}/patterns/${id}`);
        return await response.json();
    }

    // 数据采集相关API
    static async crawlData() {
        const response = await fetch(`${this.baseURL}/crawl`, {
            method: 'POST'
        });
        return await response.json();
    }

    // 股票数据相关API
    static async getStocks() {
        const response = await fetch(`${this.baseURL}/stocks`);
        return await response.json();
    }

    static async getStockPrice(stockCode, days = 30) {
        const response = await fetch(`${this.baseURL}/stocks/${stockCode}/price?days=${days}`);
        return await response.json();
    }

    // 系统状态检查
    static async getStatus() {
        const response = await fetch(`${this.baseURL}/status`);
        return await response.json();
    }
}