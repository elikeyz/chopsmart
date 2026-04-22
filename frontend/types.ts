export interface Recipe {
  name: string;
  ingredients: {
    name: string;
    quantity: string;
    unit: string;
  }[];
  steps: string[];
  calories: number;
  suggestions: string[];
}
