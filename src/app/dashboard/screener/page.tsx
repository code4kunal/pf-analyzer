'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
import { useTable, useSortBy } from 'react-table';

interface StockData {
  Stock: string;
  Rank: number;
  Latest_Price: number;
  '1M_Return_Normalized': number;
  '3M_Return_Normalized': number;
  '6M_Return_Normalized': number;
  Strength_Score_Normalized: number;
  '20_MA': number;
  '20_MAV': number;
  Liquidity: number;
}

export default function ScreenerPage() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [loading, setLoading] = useState(true);
  const [backtestDate, setBacktestDate] = useState('');
  const [backtestResults, setBacktestResults] = useState<StockData[]>([]);
  const [showBacktest, setShowBacktest] = useState(false);

  const columns = [
    { Header: 'Stock', accessor: 'Stock' },
    { Header: 'Rank', accessor: 'Rank' },
    { Header: 'Latest Price', accessor: 'Latest_Price' },
    { Header: '1M Return', accessor: '1M_Return_Normalized' },
    { Header: '3M Return', accessor: '3M_Return_Normalized' },
    { Header: '6M Return', accessor: '6M_Return_Normalized' },
    { Header: 'Strength Score', accessor: 'Strength_Score_Normalized' },
    { Header: '20 MA', accessor: '20_MA' },
    { Header: '20 MAV', accessor: '20_MAV' },
    { Header: 'Liquidity', accessor: 'Liquidity' },
  ];

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable(
    {
      columns,
      data: showBacktest ? backtestResults : stocks,
    },
    useSortBy
  );

  useEffect(() => {
    const fetchStocks = async () => {
      try {
        const response = await axios.get('http://localhost:8000/run-backtest', {
          params: { date: new Date().toISOString().split('T')[0] },
        });
        setStocks(response.data.results);
      } catch (error) {
        console.error('Error fetching stocks:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStocks();
  }, []);

  const handleBacktest = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:8000/run-backtest', {
        params: { date: backtestDate },
      });
      setBacktestResults(response.data.results);
      setShowBacktest(true);
    } catch (error) {
      console.error('Error running backtest:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Backtest
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>Run backtest for a specific date.</p>
          </div>
          <div className="mt-5">
            <div className="flex items-center space-x-4">
              <input
                type="date"
                value={backtestDate}
                onChange={(e) => setBacktestDate(e.target.value)}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-48 sm:text-sm border-gray-300 rounded-md"
              />
              <button
                type="button"
                onClick={handleBacktest}
                disabled={!backtestDate || loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Run Backtest
              </button>
              {showBacktest && (
                <button
                  type="button"
                  onClick={() => setShowBacktest(false)}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Show Current Data
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow sm:rounded-lg overflow-hidden">
        <div className="px-4 py-5 sm:p-6">
          <div className="overflow-x-auto">
            <table {...getTableProps()} className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                {headerGroups.map((headerGroup) => (
                  <tr {...headerGroup.getHeaderGroupProps()}>
                    {headerGroup.headers.map((column) => (
                      <th
                        {...column.getHeaderProps(column.getSortByToggleProps())}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {column.render('Header')}
                        <span>
                          {column.isSorted
                            ? column.isSortedDesc
                              ? ' 🔽'
                              : ' 🔼'
                            : ''}
                        </span>
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody
                {...getTableBodyProps()}
                className="bg-white divide-y divide-gray-200"
              >
                {rows.map((row) => {
                  prepareRow(row);
                  return (
                    <tr {...row.getRowProps()}>
                      {row.cells.map((cell) => (
                        <td
                          {...cell.getCellProps()}
                          className="px-6 py-4 whitespace-nowrap text-sm text-gray-500"
                        >
                          {cell.render('Cell')}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
} 