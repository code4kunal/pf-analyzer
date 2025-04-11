'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';

interface StockData {
  Stock: string;
  Latest_Price: number;
  '1M_Return': number;
  '3M_Return': number;
  '6M_Return': number;
  Volume: number;
  Strength_Score: number;
  '20_MA': number;
  '50_MA': number;
  '200_MA': number;
}

export default function DashboardPage() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { user, logout } = useAuth();

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }

    const fetchStocks = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/stock-data');
        setStocks(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching stock data:', error);
        setLoading(false);
      }
    };

    fetchStocks();
  }, [user, router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (!user) {
    return null; // Don't render anything while redirecting
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Stock Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">Logged in as: {user.id}</span>
            <button
              onClick={handleLogout}
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
            >
              Logout
            </button>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">1M Return</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">3M Return</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">6M Return</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Volume</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Strength Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">20 MA</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">50 MA</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">200 MA</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {stocks.map((stock) => (
                  <tr key={stock.Stock}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{stock.Stock}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock.Latest_Price}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock['1M_Return']}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock['3M_Return']}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock['6M_Return']}%</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock.Volume}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock.Strength_Score}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock['20_MA']}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock['50_MA']}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{stock['200_MA']}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
} 