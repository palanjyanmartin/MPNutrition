import streamlit as st
import openai
import pandas as pd
import random
from datetime import datetime
import os

# --- App Config ---
st.set_page_config(page_title="Nutrition Assistant", page_icon="🥗")
client = openai.OpenAI(api_key="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")

# --- CSV for History ---
history_file = "/Users/martinpalanjyan/Desktop/recipe_history.csv"

def initialize_csv():
    if not pd.io.common.file_exists(history_file):
        df = pd.DataFrame(columns=["recipeName", "ingredients", "nutritionInfo", "mealType", "timestamp"])
        df.to_csv(history_file, index=False)

initialize_csv()

# --- Classify Meal Type ---
def classify_meal_type(recipe_name, ingredients):
    prompt = f"""
    Classify the following recipe into one of the meal types: Breakfast, Lunch, or Dinner.
    Recipe name: {recipe_name}
    Ingredients: {ingredients}
    
    Provide only the meal type (Breakfast, Lunch, or Dinner).
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert in meal classification."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e} "

# --- Estimate Nutrition Info ---
def estimate_nutrition_gpt(recipe_name, ingredients):
    prompt = f"""
    You are a fun and concise nutrition expert! Given the recipe '{recipe_name}' and the ingredients:
    {ingredients}
    
    Provide a short and engaging response including:
    - Calories 
    - Fat (g) 
    - Carbs (g) 
    - Protein (g) 
    - Servings 
    - A one-line health tip 
    
    Keep it **brief, fun, easy to read, with emojis**!
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a concise and fun nutrition expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e} "

# --- Store Recipe to CSV ---
def store_recipe(recipe_name, ingredients, result, meal_type):
    if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
        df = pd.read_csv(history_file)
    else:
        df = pd.DataFrame(columns=["recipeName", "ingredients", "nutritionInfo", "mealType", "timestamp"])

    new_data = {
        "recipeName": recipe_name,
        "ingredients": ingredients,
        "nutritionInfo": result,
        "mealType": meal_type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(history_file, index=False)

def generate_recipe_from_history(meal_type):
    try:
        # Load the history file with fallback columns
        if os.path.exists(history_file) and os.path.getsize(history_file) > 0:
            df = pd.read_csv(history_file)

            # Ensure all necessary columns exist
            expected_cols = ["recipeName", "ingredients", "nutritionInfo", "mealType", "timestamp"]
            for col in expected_cols:
                if col not in df.columns:
                    st.error(f"Missing expected column: `{col}`. Please reset your history file.")
                    return
        else:
            st.error("No recipes stored yet. Please add some recipes first.")
            return

        # Filter by meal type
        meal_recipes = df[df["mealType"].str.lower() == meal_type.lower()]

        if meal_recipes.empty:
            st.warning(f"No recipes found for {meal_type}. Try adding more recipes!")
        else:
            random_recipe = meal_recipes.sample(n=1).iloc[0]
            st.subheader(f"🍽️ {random_recipe['recipeName']}")
            st.write(f"**Ingredients:** {random_recipe['ingredients']}")
            st.markdown(random_recipe['nutritionInfo'])  # Markdown for better formatting
            st.write(f"**Meal Type:** {random_recipe['mealType']}")

    except Exception as e:
        st.error(f"An error occurred while loading recipe history: {e}")

# --- Generate New Recipe from Preference ---
def generate_recipe_from_preferences(preference_text):
    prompt = f"""
    Generate a creative and healthy recipe based on the preference:
    "{preference_text}"
    
    Return:
    - A catchy recipe name 🍽️
    - Ingredients with amounts 📝
    - Cooking steps 🧑‍🍳
    - Macronutrient info per serving 🔢
    - A short fun fact 🤓

    Make it easy to read, not too long, and engaging!
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative and engaging recipe generator."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e} 😞"

# --- Sidebar Navigation ---
st.sidebar.title("🍽️ Navigation")
page = st.sidebar.radio("Go to", ["🥗 Estimate Nutrition", "🍝 Generate Recipe by Preference"])

# --- Page 1: Estimate Nutrition ---
if page == "🥗 Estimate Nutrition":
    st.title("🥗 Recipe Calorie Estimator")
    st.write("Enter a recipe name and ingredients to get a quick, fun nutritional breakdown!")

    recipe_name = st.text_input("📌 Recipe Name")
    ingredients_input = st.text_area("📝 Ingredients (e.g. chicken breast: 200g, rice: 100g)")

    if st.button("🔍 Estimate Nutrition"):
        if recipe_name and ingredients_input:
            result = estimate_nutrition_gpt(recipe_name, ingredients_input)
            st.subheader("🍽️ Nutritional Breakdown")
            st.markdown(result)

            meal_type = classify_meal_type(recipe_name, ingredients_input)
            st.write(f"🍽️ This recipe is classified as: **{meal_type}**")

            store_recipe(recipe_name, ingredients_input, result, meal_type)
            st.success("✅ Recipe saved to history!")
        else:
            st.error("⚠️ Please enter both fields!")

    st.markdown("---")
    st.subheader("📚 Suggest Me a Recipe from History")
    meal_type = st.selectbox("Choose meal type", ["Breakfast", "Lunch", "Dinner"])
    if st.button("🌀 Generate Recipe Based On History"):
        generate_recipe_from_history(meal_type)

    if st.checkbox("📜 Show Recent Recipes"):
        df = pd.read_csv(history_file)
        st.dataframe(df.tail(5))

# --- Page 2: Generate Recipe ---
elif page == "🍝 Generate Recipe by Preference":
    st.title("🍝 Generate Recipes Based on Preferences")
    st.write("Describe what kind of meal you want, and I’ll cook up something just for you! 🍳")

    user_input = st.text_area("📝 Example: Light dinner with high protein, or healthy Italian lunch under 400 calories.")

    if st.button("🍽️ Generate Recipe"):
        if user_input:
            result = generate_recipe_from_preferences(user_input)
            st.subheader("👨‍🍳 Your Recipe")
            st.markdown(result)
        else:
            st.error("⚠️ Please describe your preference first!")
