import 'react-native';
import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import App from '../App';

describe('App root navigation', () => {
  const responses: Record<string, any> = {
    '/inventory': [
      { id: '1', name: 'Milk', quantity: 1, unit: 'liters', expires_on: '2024-06-01' },
    ],
    '/recipes': [
      { id: '1', title: 'Pancakes', ingredients: [], instructions: '' },
    ],
    '/meal-plans?week_start=auto': {
      week_start: '2024-05-27',
      entries: [],
    },
    '/shopping-list?week_start=auto': {
      items: [
        { name: 'Eggs', quantity: 6, unit: 'count' },
      ],
    },
  };

  beforeEach(() => {
    global.fetch = jest.fn(async (url: string) => {
      const path = url.replace('http://localhost:8000', '');

      // Handle meal plans and shopping lists with dynamic week_start
      let key = path;
      if (path.startsWith('/meal-plans?week_start=')) {
        key = '/meal-plans?week_start=auto';
      } else if (path.startsWith('/shopping-list?week_start=')) {
        key = '/shopping-list?week_start=auto';
      }

      if (!(key in responses)) {
        throw new Error(`Unexpected fetch ${url}`);
      }
      return {
        ok: true,
        json: async () => responses[key],
      } as Response;
    });
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('renders the primary tabs', async () => {
    const { getByText } = render(<App />);

    await waitFor(() => {
      expect(getByText('Inventory')).toBeTruthy();
      expect(getByText('Recipes')).toBeTruthy();
      expect(getByText('Meal Plan')).toBeTruthy();
      expect(getByText('Shopping List')).toBeTruthy();
    });
  });

  it('displays fetched inventory data', async () => {
    const { findByText } = render(<App />);
    expect(await findByText('Milk — 1 liters')).toBeTruthy();
  });
});
