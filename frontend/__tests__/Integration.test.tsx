import 'react-native';
import React from 'react';
import { render, waitFor, fireEvent } from '@testing-library/react-native';
import App from '../App';

// TypeScript declaration for Jest globals
declare const global: any;

describe('Full app integration tests', () => {
    const mockResponses: Record<string, any> = {
        '/inventory': [
            { id: '1', name: 'Milk', quantity: 2, unit: 'liters', expires_on: '2024-06-01' },
            { id: '2', name: 'Cheese', quantity: 200, unit: 'g', expires_on: null },
        ],
        '/recipes': [
            { id: '1', title: 'Pancakes', ingredients: [{ name: 'Milk', quantity: 1, unit: 'cup' }], instructions: 'Mix and cook' },
            { id: '2', title: 'Omelette', ingredients: [{ name: 'Eggs', quantity: 3 }], instructions: 'Beat and fry' },
        ],
        '/meal-plans?week_start=auto': {
            id: 'plan1',
            week_start: '2024-05-27',
            entries: [
                { day: 'monday', meal: 'breakfast', recipe_id: '1', recipe_title: 'Pancakes', servings: 2 },
            ],
        },
        '/shopping-list?week_start=auto': {
            items: [
                { name: 'Eggs', quantity: 6, unit: 'count' },
                { name: 'Flour', quantity: 200, unit: 'g' },
            ],
        },
    };

    beforeEach(() => {
        global.fetch = jest.fn(async (url: string, options?: any) => {
            const path = url.replace('http://localhost:8000', '');

            // Handle POST to /inventory
            if (path === '/inventory' && options?.method === 'POST') {
                const body = JSON.parse(options.body);
                return {
                    ok: true,
                    json: async () => ({ id: '3', ...body }),
                } as Response;
            }

            let key = path;
            if (path.startsWith('/meal-plans?week_start=')) {
                key = '/meal-plans?week_start=auto';
            } else if (path.startsWith('/shopping-list?week_start=')) {
                key = '/shopping-list?week_start=auto';
            }

            if (!(key in mockResponses)) {
                throw new Error(`Unexpected fetch ${url}`);
            }
            return {
                ok: true,
                json: async () => mockResponses[key],
            } as Response;
        });
    });

    afterEach(() => {
        jest.resetAllMocks();
    });

    describe('Navigation', () => {
        it('renders all tab navigation buttons', async () => {
            const { getByText } = render(<App />);

            await waitFor(() => {
                expect(getByText('Inventory')).toBeTruthy();
                expect(getByText('Recipes')).toBeTruthy();
                expect(getByText('Meal Plan')).toBeTruthy();
                expect(getByText('Shopping List')).toBeTruthy();
            });
        });
    });

    describe('Inventory Screen', () => {
        it('displays inventory items', async () => {
            const { findByText } = render(<App />);

            expect(await findByText('Milk — 2 liters')).toBeTruthy();
            expect(await findByText('Cheese — 200 g')).toBeTruthy();
        });

        it('shows expiration date when available', async () => {
            const { findByText } = render(<App />);

            expect(await findByText('Expires 2024-06-01')).toBeTruthy();
        });
    });

    describe('Recipes Screen', () => {
        it('displays recipe list', async () => {
            const { getByText, findByText, findAllByText } = render(<App />);

            fireEvent.press(getByText('Recipes'));

            expect(await findByText('Pancakes')).toBeTruthy();
            expect(await findByText('Omelette')).toBeTruthy();
            expect(await findAllByText('1 ingredients')).toHaveLength(2);
        });

        it('shows empty state when no recipes', async () => {
            mockResponses['/recipes'] = [];

            const { getByText, findByText } = render(<App />);

            fireEvent.press(getByText('Recipes'));

            expect(await findByText('Save recipes to get started.')).toBeTruthy();
        });
    });

    describe('Meal Plan Screen', () => {
        it('displays meal plan entries', async () => {
            const { getByText, findByText } = render(<App />);

            fireEvent.press(getByText('Meal Plan'));

            expect(await findByText('Monday Breakfast')).toBeTruthy();
            expect(await findByText('Pancakes')).toBeTruthy();
        });

        it('shows empty state when no meal plan', async () => {
            mockResponses['/meal-plans?week_start=auto'] = {
                id: 'plan1',
                week_start: '2024-05-27',
                entries: [],
            };

            const { getByText, findByText } = render(<App />);

            fireEvent.press(getByText('Meal Plan'));

            expect(await findByText('Plan your meals to generate a shopping list.')).toBeTruthy();
        });
    });

    describe('Shopping List Screen', () => {
        it('displays shopping list items', async () => {
            const { getByText, findByText } = render(<App />);

            fireEvent.press(getByText('Shopping List'));

            expect(await findByText('Eggs — 6 count')).toBeTruthy();
            expect(await findByText('Flour — 200 g')).toBeTruthy();
        });

        it('shows empty state when nothing to buy', async () => {
            mockResponses['/shopping-list?week_start=auto'] = { items: [] };

            const { getByText, findByText } = render(<App />);

            fireEvent.press(getByText('Shopping List'));

            expect(await findByText('You are stocked up. No shopping needed!')).toBeTruthy();
        });
    });

    describe('Error Handling', () => {
        it('displays error when fetch fails', async () => {
            global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

            const { findByText } = render(<App />);

            expect(await findByText('Network error')).toBeTruthy();
        });
    });
});
