'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';

interface AnalyticsData {
  totalStocks: number;
  averageReturns: {
    oneMonth: number;
    threeMonth: number;
    sixMonth: number;
  };
  topPerformers: {
    stock: string;
    return: number;
  }[];
  sectorDistribution: {
    sector: string;
    count: number;
  }[];
}

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const response = await axios.get('http://localhost:8000/run-backtest', {
          params: { date: new Date().toISOString().split('T')[0] },
        });
        
        const stocks = response.data.results;
        const totalStocks = stocks.length;
        const averageReturns = {
          oneMonth: stocks.reduce((acc: number, stock: any) => acc + stock['1M_Return_Normalized'], 0) / totalStocks,
          threeMonth: stocks.reduce((acc: number, stock: any) => acc + stock['3M_Return_Normalized'], 0) / totalStocks,
          sixMonth: stocks.reduce((acc: number, stock: any) => acc + stock['6M_Return_Normalized'], 0) / totalStocks,
        };
        
        const topPerformers = stocks
          .sort((a: any, b: any) => b.Strength_Score_Normalized - a.Strength_Score_Normalized)
          .slice(0, 5)
          .map((stock: any) => ({
            stock: stock.Stock,
            return: stock.Strength_Score_Normalized,
          }));

        setAnalytics({
          totalStocks,
          averageReturns,
          topPerformers,
          sectorDistribution: [], // This would require additional data
        });
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center text-red-500">
        Failed to load analytics data
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Total Stocks
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {analytics.totalStocks}
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Average 1M Return
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {analytics.averageReturns.oneMonth.toFixed(2)}%
            </dd>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <dt className="text-sm font-medium text-gray-500 truncate">
              Average 3M Return
            </dt>
            <dd className="mt-1 text-3xl font-semibold text-gray-900">
              {analytics.averageReturns.threeMonth.toFixed(2)}%
            </dd>
          </div>
        </div>
      </div>

      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Top Performers
          </h3>
          <div className="mt-5">
            <div className="flow-root">
              <ul className="-mb-8">
                {analytics.topPerformers.map((performer, index) => (
                  <li key={performer.stock}>
                    <div className="relative pb-8">
                      {index !== analytics.topPerformers.length - 1 && (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      )}
                      <div className="relative flex space-x-3">
                        <div>
                          <span className="h-8 w-8 rounded-full bg-indigo-500 flex items-center justify-center ring-8 ring-white">
                            <span className="text-white font-medium">
                              {index + 1}
                            </span>
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-sm text-gray-500">
                              {performer.stock}{' '}
                              <span className="font-medium text-gray-900">
                                {performer.return.toFixed(2)}%
                              </span>
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 