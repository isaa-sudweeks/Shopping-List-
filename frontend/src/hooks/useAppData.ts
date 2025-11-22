import { useCallback, useEffect, useState } from 'react';

export type InventoryItem = {
  id: string;
  name: string;
  quantity: number;
  unit?: string | null;
  expires_on?: string | null;
};

export type Recipe = {
  id: string;
  title: string;
  instructions?: string | null;
  ingredients: Array<{
    name: string;
    quantity: number;
    unit?: string | null;
  }>;
};

export type MealPlanEntry = {
  day: string;
  meal: string;
  recipe_id: string;
  recipe_title: string;
  servings: number;
};

export type MealPlan = {
  id: string;
  week_start: string;
  entries: MealPlanEntry[];
};

export type ShoppingListItem = {
  name: string;
  quantity: number;
  unit?: string | null;
};

const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

function getCurrentWeekStart(): string {
  const now = new Date();
  const day = now.getDay(); // 0 is Sunday
  const diff = now.getDate() - day + (day === 0 ? -6 : 1); // Adjust when day is Sunday
  const monday = new Date(now.setDate(diff));
  return monday.toISOString().split('T')[0];
}

const DEFAULT_WEEK_START = getCurrentWeekStart();

type AppDataState = {
  inventory: InventoryItem[];
  recipes: Recipe[];
  mealPlan: MealPlan | null;
  shoppingList: ShoppingListItem[];
  loading: boolean;
  error?: string;
};

const initialState: AppDataState = {
  inventory: [],
  recipes: [],
  mealPlan: null,
  shoppingList: [],
  loading: true,
  error: undefined,
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function useAppData() {
  const [state, setState] = useState<AppDataState>(initialState);

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: undefined }));
    try {
      const [inventory, recipes] = await Promise.all([
        fetchJson<InventoryItem[]>('/inventory'),
        fetchJson<Recipe[]>('/recipes'),
      ]);

      let mealPlan: MealPlan | null = null;
      try {
        mealPlan = await fetchJson<MealPlan | null>(`/meal-plans?week_start=${DEFAULT_WEEK_START}`);
      } catch (e) {
        if (!(e instanceof Error && e.message.includes('404'))) {
          throw e;
        }
      }

      let shoppingList: ShoppingListItem[] = [];
      try {
        const result = await fetchJson<{ items: ShoppingListItem[] }>(
          `/shopping-list?week_start=${DEFAULT_WEEK_START}`,
        );
        shoppingList = result.items;
      } catch (e) {
        if (!(e instanceof Error && e.message.includes('404'))) {
          throw e;
        }
      }

      setState({
        inventory,
        recipes,
        mealPlan,
        shoppingList,
        loading: false,
        error: undefined,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { ...state, refresh: load };
}
