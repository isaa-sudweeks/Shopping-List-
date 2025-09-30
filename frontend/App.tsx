import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import {
  ActivityIndicator,
  FlatList,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useAppData } from './src/hooks/useAppData';

const Tab = createBottomTabNavigator();

function formatQuantity(quantity: number): string {
  if (Number.isInteger(quantity)) {
    return quantity.toString();
  }
  return quantity.toFixed(2).replace(/\.00$/, '');
}

const InventoryScreen = ({
  loading,
  error,
  inventory,
}: {
  loading: boolean;
  error?: string;
  inventory: ReturnType<typeof useAppData>['inventory'];
}) => {
  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {error ? <Text style={styles.errorText}>{error}</Text> : null}
      <FlatList
        data={inventory}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.listItem}>
            <Text style={styles.itemTitle}>
              {`${item.name} \u2014 ${formatQuantity(item.quantity)}${item.unit ? ` ${item.unit}` : ''}`}
            </Text>
            {item.expires_on ? <Text style={styles.secondary}>Expires {item.expires_on}</Text> : null}
          </View>
        )}
        ListEmptyComponent={<Text style={styles.secondary}>No items in your pantry.</Text>}
      />
    </SafeAreaView>
  );
};

const RecipesScreen = ({
  loading,
  error,
  recipes,
}: {
  loading: boolean;
  error?: string;
  recipes: ReturnType<typeof useAppData>['recipes'];
}) => (
  <SafeAreaView style={styles.container}>
    {loading ? <ActivityIndicator /> : null}
    {error ? <Text style={styles.errorText}>{error}</Text> : null}
    <ScrollView>
      {recipes.map((recipe) => (
        <View key={recipe.id} style={styles.listItem}>
          <Text style={styles.itemTitle}>{recipe.title}</Text>
          <Text style={styles.secondary}>{recipe.ingredients.length} ingredients</Text>
        </View>
      ))}
      {!recipes.length && !loading ? <Text style={styles.secondary}>Save recipes to get started.</Text> : null}
    </ScrollView>
  </SafeAreaView>
);

const MealPlanScreen = ({
  loading,
  error,
  mealPlan,
}: {
  loading: boolean;
  error?: string;
  mealPlan: ReturnType<typeof useAppData>['mealPlan'];
}) => (
  <SafeAreaView style={styles.container}>
    {loading ? <ActivityIndicator /> : null}
    {error ? <Text style={styles.errorText}>{error}</Text> : null}
    {mealPlan && mealPlan.entries.length ? (
      <ScrollView>
        {mealPlan.entries.map((entry) => (
          <View key={`${entry.day}-${entry.meal}`} style={styles.listItem}>
            <Text style={styles.itemTitle}>
              {`${capitalize(entry.day)} ${capitalize(entry.meal)}`}
            </Text>
            <Text style={styles.secondary}>{entry.recipe_title}</Text>
          </View>
        ))}
      </ScrollView>
    ) : (
      <Text style={styles.secondary}>Plan your meals to generate a shopping list.</Text>
    )}
  </SafeAreaView>
);

const ShoppingListScreen = ({
  loading,
  error,
  shoppingList,
}: {
  loading: boolean;
  error?: string;
  shoppingList: ReturnType<typeof useAppData>['shoppingList'];
}) => (
  <SafeAreaView style={styles.container}>
    {loading ? <ActivityIndicator /> : null}
    {error ? <Text style={styles.errorText}>{error}</Text> : null}
    <ScrollView>
      {shoppingList.map((item) => (
        <View key={`${item.name}-${item.unit ?? 'none'}`} style={styles.listItem}>
          <Text style={styles.itemTitle}>
            {`${item.name} \u2014 ${formatQuantity(item.quantity)}${item.unit ? ` ${item.unit}` : ''}`}
          </Text>
        </View>
      ))}
      {!shoppingList.length && !loading ? (
        <Text style={styles.secondary}>You are stocked up. No shopping needed!</Text>
      ) : null}
    </ScrollView>
  </SafeAreaView>
);

function capitalize(value: string) {
  if (!value) {
    return value;
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export default function App(): React.ReactElement {
  const data = useAppData();

  return (
    <NavigationContainer>
      <Tab.Navigator screenOptions={{ headerShown: false }}>
        <Tab.Screen name="Inventory">
          {() => <InventoryScreen {...data} />}
        </Tab.Screen>
        <Tab.Screen name="Recipes">
          {() => <RecipesScreen {...data} />}
        </Tab.Screen>
        <Tab.Screen name="Meal Plan">
          {() => <MealPlanScreen {...data} />}
        </Tab.Screen>
        <Tab.Screen name="Shopping List">
          {() => <ShoppingListScreen {...data} />}
        </Tab.Screen>
      </Tab.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#fff',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listItem: {
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#ddd',
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  secondary: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  errorText: {
    color: '#b00020',
    marginBottom: 12,
  },
});
