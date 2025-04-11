import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useTable } from 'react-table';
import './App.css';

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

function App() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
  }, []);

  const columns = React.useMemo(
    () => [
      { Header: 'Stock', accessor: 'Stock' },
      { Header: 'Price', accessor: 'Latest_Price' },
      { Header: '1M Return', accessor: '1M_Return' },
      { Header: '3M Return', accessor: '3M_Return' },
      { Header: '6M Return', accessor: '6M_Return' },
      { Header: 'Volume', accessor: 'Volume' },
      { Header: 'Strength Score', accessor: 'Strength_Score' },
      { Header: '20 MA', accessor: '20_MA' },
      { Header: '50 MA', accessor: '50_MA' },
      { Header: '200 MA', accessor: '200_MA' },
    ],
    []
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable({ columns, data: stocks });

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="App">
      <h1>Stock Dashboard</h1>
      <div className="table-container">
        <table {...getTableProps()}>
          <thead>
            {headerGroups.map(headerGroup => (
              <tr {...headerGroup.getHeaderGroupProps()}>
                {headerGroup.headers.map(column => (
                  <th {...column.getHeaderProps()}>
                    {column.render('Header')}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody {...getTableBodyProps()}>
            {rows.map(row => {
              prepareRow(row);
              return (
                <tr {...row.getRowProps()}>
                  {row.cells.map(cell => (
                    <td {...cell.getCellProps()}>
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
  );
}

export default App; 