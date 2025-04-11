'use client';

import { useState } from 'react';
import axios from 'axios';

export default function DataPage() {
  const [days, setDays] = useState(30);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleLoadHistorical = async () => {
    try {
      setLoading(true);
      setMessage('');
      const response = await axios.post('http://localhost:8000/load-historical-data', {
        days,
      });
      setMessage(`Success: ${response.data.message}`);
    } catch (error) {
      setMessage('Error loading historical data');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadToday = async () => {
    try {
      setLoading(true);
      setMessage('');
      const response = await axios.post('http://localhost:8000/add-todays-data', {
        file_path: '/Users/kunalsaxena/stocks/stock_data/historical_data.csv',
      });
      setMessage(`Success: ${response.data.message}`);
    } catch (error) {
      setMessage('Error loading today\'s data');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Load Historical Data
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>Load historical data for the specified number of days.</p>
          </div>
          <div className="mt-5">
            <div className="flex items-center space-x-4">
              <input
                type="number"
                value={days}
                onChange={(e) => setDays(Number(e.target.value))}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-32 sm:text-sm border-gray-300 rounded-md"
                min="1"
              />
              <button
                type="button"
                onClick={handleLoadHistorical}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                {loading ? 'Loading...' : 'Load Historical Data'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Load Today's Data
          </h3>
          <div className="mt-2 max-w-xl text-sm text-gray-500">
            <p>Add today's data to the existing historical data file.</p>
          </div>
          <div className="mt-5">
            <button
              type="button"
              onClick={handleLoadToday}
              disabled={loading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {loading ? 'Loading...' : 'Load Today\'s Data'}
            </button>
          </div>
        </div>
      </div>

      {message && (
        <div
          className={`rounded-md p-4 ${
            message.includes('Error')
              ? 'bg-red-50 text-red-700'
              : 'bg-green-50 text-green-700'
          }`}
        >
          {message}
        </div>
      )}
    </div>
  );
} 